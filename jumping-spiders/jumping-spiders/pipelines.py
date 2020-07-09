# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
import scrapy
import hashlib
import mimetypes
import re
import uuid
import pdfplumber
import boto3
import pandas as pd
from io import StringIO
from price_parser import Price
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem, NotConfigured
from scrapy.utils.python import to_bytes
from urllib.parse import urlparse
from food_products.utils.database import get_session
from food_products.utils.dates import get_date_range_form_url


class BasicBasketsDuplicatesFilterPipeline:

    def process_item(self, item, spider):
        settings = spider.settings['DATABASE_SETTINGS']
        session = get_session(**settings)

        file_urls = []

        for file_url in item['file_urls']:
            file_hash = hashlib.sha1(to_bytes(file_url)).hexdigest()
            result = session.execute(
                """SELECT 1 FROM basic_baskets_indexing WHERE file_hash = :file_hash LIMIT 1""", {
                    'file_hash': file_hash
                }).scalar()

            if not result:
                file_urls.append(file_url)

        item['file_urls'] = file_urls

        return item


class BasicBasketsPdfsDownloadPipeline(FilesPipeline):

    def file_path(self, request, response=None, info=None):
        media_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        media_ext = os.path.splitext(request.url)[1]
        # Handles empty and wild extensions by trying to guess the
        # mime type then extension or default to empty string otherwise
        if media_ext not in mimetypes.types_map:
            media_ext = ''
            media_type = mimetypes.guess_type(request.url)[0]
            if media_type:
                media_ext = mimetypes.guess_extension(media_type)

        media_path = '{}{}'.format(media_guid, media_ext)
        return media_path

    def get_media_requests(self, item, info):
        for file_url in item['file_urls']:
            yield scrapy.Request(file_url)

    def item_completed(self, results, item, info):
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")
        item['file_paths'] = file_paths
        return item


class BasicBasketsPdfsToCsvsPipeline:

    excluded_columns_regex = re.compile(
        r'(n0|Resumen General Media y/o|Promedio Global|Precios|Mínimo|Precios|Máximo|Moda|Mediana|Desviación|Estándar)', re.I)

    def process_item(self, item, spider):
        fs_store = spider.settings['FILES_STORE']
        file_outputs = []

        for file_path, file_url in zip(item['file_paths'], item['file_urls']):
            spider.logger.info('Parsing: %s', file_path)

            file_output = self.pdf_to_csv(
                '{}{}'.format(fs_store, file_path),
                file_url)

            file_outputs.append(file_output)

        item['file_outputs'] = file_outputs

        return item

    def pdf_to_csv(self, file_path, file_url):
        path, ext = os.path.splitext(file_path)
        name = os.path.basename(path)
        file_output = '{}{}'.format(path, '.csv')

        if os.path.exists(file_output):
            return file_output

        start_date, end_date = get_date_range_form_url(file_url)

        pages = []

        with pdfplumber.open(file_path) as pdf:

            for page in pdf.pages:
                # extract table from every page individually.
                # pdf can have fixed headers and this messes up with
                # the implementation.
                tables = page.extract_tables()

                # pdfplumber cloud return multiple tables for the same
                # table instance in the pdf
                df = pd.concat([pd.DataFrame(table)
                                for table in tables], axis=1)

                # export and read csv to merge header rows.
                output = StringIO(df.to_csv(header=False, index=False))
                df = pd.read_csv(output, header=[0, 1, 2])
                df.columns = df.columns.map(lambda h: '{} {} {}'.format(
                    h[0], h[1], h[2]).replace('\n', '|'))

                df.rename_axis('id')
                df.fillna(' ', inplace=True)

                # excludes irrelevant columns
                excluded_columns = [df.columns.get_loc(
                    c) for c in df.columns if self.excluded_columns_regex.search(c)]
                df.drop(df.columns[excluded_columns], axis=1, inplace=True)

                items = pd.DataFrame(data=None, columns=['id', 'file_id', 'description', 'unit',
                                                         'vendor', 'price', 'currency', 'start_date',
                                                         'end_date'])

                # read pivoted (product x vendor) data
                for index, row in df.iterrows():
                    description = str(row[0]).strip()
                    unit = str(row[1]).strip()

                    if (not description or not unit):
                        continue

                    for (label, contents) in df[df.columns[2:]].iteritems():
                        value = contents.at[index]
                        price = Price.fromstring(str(value))
                        if not price.amount:
                            continue

                        vendor = re.sub(
                            r'Unnamed:\s\d{1,2}_level_\d{1,2}', '', label)

                        item = {
                            'id': uuid.uuid4(),
                            'file_id': name,
                            'description': description,
                            'unit': unit,
                            'vendor': vendor,
                            'price': price.amount,
                            'currency': 'DOP',
                            'start_date': start_date,
                            'end_date': end_date
                        }

                        items = items.append(item, ignore_index=True)

                pages.append(items)

            pdf.close()

        pd.concat(pages).to_csv(file_output, index=False)

        return file_output


class BasicBasketsFilesUploadPipeline:
    def process_item(self, item, spider):
        client = boto3.client('s3')

        fs_store = spider.settings['FILES_STORE']
        s3_store = spider.settings['FILES_STORE_S3']

        bucket, prefix = s3_store[5:].split('/', 1)

        for file_path, file_output in zip(item['file_paths'], item['file_outputs']):
            spider.logger.info('Uploading: %s', file_path)

            client.upload_file('{}{}'.format(fs_store, file_path),
                               bucket,
                               '{}{}'.format(prefix, file_path))

            spider.logger.info('Uploading: %s', file_output)

            client.upload_file(file_output,
                               bucket,
                               '{}{}'.format(prefix, os.path.basename(file_output)))

        return item


class BasicBasketsPdfsIndexingPipeline:
    def process_item(self, item, spider):
        settings = spider.settings['DATABASE_SETTINGS']
        session = get_session(**settings)

        for (file_url, file_path) in zip(item['file_urls'], item['file_paths']):
            file_hash = os.path.splitext(os.path.basename(file_path))[0]

            session.execute("""INSERT INTO basic_baskets_indexing (file_hash, file_url) 
                VALUES (:file_hash, :file_url)""", {
                'file_hash': file_hash,
                'file_url': file_url,
            })

        session.commit()

        return item
