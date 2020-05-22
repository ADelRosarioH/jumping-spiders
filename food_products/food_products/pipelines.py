# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
import scrapy
import boto3
import hashlib
import mimetypes
import pdfplumber
import re
import uuid
import pandas as pd

from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
from scrapy.utils.python import to_bytes
from urllib.parse import urlparse
from io import StringIO
from price_parser import Price
from slugify import slugify
from .utils.dates import get_date_range


class BasicBasketsPdfDownloadPipeline(FilesPipeline):

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
        print(results)
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")
        item['file_paths'] = file_paths
        return item


class BasicBasketsPdfProcessingPipeline:
    excluded_columns_regex = re.compile(
        r'(n0|Resumen General Media y/o|Promedio Global|Precios|Mínimo|Precios|Máximo|Moda|Mediana|Desviación|Estándar)', re.I)

    def process_item(self, item, spider):
        settings = get_project_settings()

        bucket, prefix = settings.get('FILES_STORE')[5:].split('/', 1)

        s3 = boto3.resource('s3')

        file_outputs = []

        for file, url in zip(item['file_paths'], item['file_urls']):

            key = '{}{}'.format(prefix, file)
            filename = '/tmp/{}'.format(file)

            if not os.path.exists(filename):
                s3.meta.client.download_file(bucket, key, filename)

            file_output = self.pdf_to_csv(filename, url)
            file_outputs.append(file_output)

        item['file_outputs'] = file_outputs

        return item

    def pdf_to_csv(self, filename, url):
        path, ext = os.path.splitext(filename)
        name = os.path.basename(path)
        file_output = '{}{}'.format(path, '.csv')

        if os.path.exists(file_output):
            return file_output

        start_date, end_date = get_date_range(url)

        pages = []

        with pdfplumber.open(filename) as pdf:

            for page in pdf.pages:
                # 1
                tables = page.extract_tables()

                df = pd.concat([pd.DataFrame(table)
                                for table in tables], axis=1)
                # 2
                # output = '{}-{}{}'.format(path, page.page_number, '.csv')
                output = StringIO(df.to_csv(header=False, index=False))

                # 3
                df = pd.read_csv(output, header=[0, 1, 2])
                df.columns = df.columns.map(lambda h: '{} {} {}'.format(
                    h[0], h[1], h[2]).replace('\n', '|'))
                df.rename_axis('id')

                df.fillna(' ', inplace=True)

                # 4
                excluded_columns = [df.columns.get_loc(
                    c) for c in df.columns if self.excluded_columns_regex.search(c)]
                df.drop(df.columns[excluded_columns], axis=1, inplace=True)

                # 5
                items = pd.DataFrame(data=None, columns=['id', 'page_id', 'description', 'unit',
                                                         'vendor_name', 'vendor_location', 'slug', 'price',
                                                         'currency', 'start_date', 'end_date'])

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

                        vendor_info = re.sub(
                            r'Unnamed:\s\d{1,2}_level_\d{1,2}', '', label).split('|')

                        vendor_name = ''
                        vendor_location = ''

                        if len(vendor_info) > 0:
                            vendor_name = vendor_info[0]

                        if len(vendor_info) > 1:
                            vendor_location = vendor_info[1]

                        item = {
                            "id": uuid.uuid4(),
                            "page_id": name,
                            "description": description,
                            "unit": unit,
                            "vendor_name": vendor_name,
                            "vendor_location": vendor_location,
                            "slug": slugify(u'{}-{}'.format(description, unit), only_ascii=True),
                            "price": price.amount,
                            "currency": 'DOP',
                            "start_date": start_date,
                            "end_date": end_date
                        }

                        items = items.append(item, ignore_index=True)

                pages.append(items)

            pdf.close()

        pd.concat(pages).to_csv(file_output, index=False)

        return file_output


class BasicBasketsPersistencePipeline:
    def process_item(self, item, spider):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('food_products')

        for file in item['file_outputs']:
            df = pd.read_csv(file)
            deserialized = df.to_json(orient='records')
            records = json.loads(deserialized, parse_float=Decimal)
            with table.batch_writer() as batch:
                for record in records:
                    batch.put_item(
                        Item=record
                    )
