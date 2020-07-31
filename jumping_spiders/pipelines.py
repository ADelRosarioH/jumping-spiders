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
from jumping_spiders.utils.database import get_session
from jumping_spiders.utils.dates import get_date_range_form_url

class FileDownloadPipeline(FilesPipeline):

    def file_path(self, request, response=None, info=None):
        media_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        media_path, media_ext = os.path.splitext(request.url)
        media_name = os.path.basename(media_path)
        # Handles empty and wild extensions by trying to guess the
        # mime type then extension or default to empty string otherwise
        if media_ext not in mimetypes.types_map:
            media_ext = ''
            media_type = mimetypes.guess_type(request.url)[0]
            if media_type:
                media_ext = mimetypes.guess_extension(media_type)

        media_path = '{}{}'.format(media_name, media_ext)
        return media_path

    def get_media_requests(self, item, info):
        fs_store = info.spider.settings['FILES_STORE']

        for file_url in item['file_urls']:
            media_guid = hashlib.sha1(to_bytes(file_url)).hexdigest()
            media_path, media_ext = os.path.splitext(file_url)
            media_name = os.path.basename(media_path)

            local_file_path = os.path.join(fs_store, media_name, media_ext)

            if not os.path.exists(local_file_path):
                yield scrapy.Request(file_url)

    def item_completed(self, results, item, info):
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")
        item['file_paths'] = file_paths
        return item


class BasicBasketsPdfsToCsvsPipeline:

    excluded_columns_regex = re.compile(
        r'(CASA EDITORIAL|n0|Resumen General Media y/o|Promedio Global|Precios|Mínimo|Precios|Máximo|Moda|Mediana|Desviación|Estándar)', re.I)

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
                # in case of hardware products, last page find a table with no cells
                if len(tables) <= 0:
                    continue

                # pdfplumber cloud return multiple tables for the same
                # table instance in the pdf
                df = pd.concat([pd.DataFrame(table)
                                for table in tables], axis=1)

                # export and read csv to merge header rows.
                df = df.replace('\n', '', regex=True)
                df.fillna('--', inplace=True)

                if len(df.index) < 3:
                    continue

                output = StringIO(df.to_csv(header=False, index=False))
                df = pd.read_csv(output, header=[0, 1, 2])
                
                df.columns = df.columns.map(lambda h: '{} {} {}'.format(
                    h[0], h[1], h[2]).replace('\n', '|'))

                df.rename_axis('id')
                
                # excludes irrelevant columns
                excluded_columns = [df.columns.get_loc(
                    c) for c in df.columns if self.excluded_columns_regex.search(c)]
                df.drop(df.columns[excluded_columns], axis=1, inplace=True)

                items = pd.DataFrame(data=None, columns=['id', 'file_id', 'description', 'unit',
                                                         'vendor', 'price', 'currency', 'start_date',
                                                         'end_date'])

                # read pivoted (product x vendor) data
                for index, row in df.iterrows():
                    if len(row) < 2:
                        continue

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


class MedicinesPdfsToCsvsPipeline:

    excluded_columns_regex = re.compile(
        r'(n0|no|Orden|Resumen|General|Media|Promedio|Global|Mínimo|Máximo|Moda|Mediana|Desviación|Estándar)', re.I)

    generic_columns_regex = re.compile(r'Genérico|Principio|Activo|Concentrac', re.I)

    commercial_columns_regex = re.compile(r'Marca|Concentrac', re.I)

    clean_columns_regex = re.compile(r'Genérico|Principio|Activo')

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
        generic_file_output = '{}-{}{}'.format(path, 'generic', ext)
        commercial_file_output = '{}-{}{}'.format(path, 'commercial', ext)

        if os.path.exists(file_output):
            return file_output

        if os.path.exists(generic_file_output):
            return file_output

        if os.path.exists(commercial_file_output):
            return file_output

        start_date, end_date = get_date_range_form_url(file_url)

        generic_report_pages = []
        commercial_report_pages = []
        single_report_pages = []

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

                output = StringIO(df.to_csv(header=False, index=False))
                df = pd.read_csv(output, header=[0, 1, 2])
                df.columns = df.columns.map(lambda h: '{} {} {}'.format(
                    h[0], h[1], h[2]).replace('\n', '|'))

                # excludes irrelevant columns
                excluded_columns = [df.columns.get_loc(
                    c) for c in df.columns if self.excluded_columns_regex.search(c)]

                df.drop(df.columns[excluded_columns], axis=1, inplace=True)

                # df = df.dropna(how='all', axis=1)

                generic_columns = [df.columns.get_loc(
                    c) for c in df.columns if self.generic_columns_regex.search(c)]

                commercial_columns = [df.columns.get_loc(
                    c) for c in df.columns if self.commercial_columns_regex.search(c)]

                if (len(generic_columns) > 1 and len(commercial_columns) > 1):
                    generic_df = df.copy()
                    generic_df.drop(
                        generic_df.columns[commercial_columns], axis=1, inplace=True)

                    cleaned_columns = [
                        re.sub(self.clean_columns_regex, '', c) for c in generic_df.columns]

                    generic_df.columns = cleaned_columns

                    generic_report_page = self.parse_report(
                        generic_df, name, start_date, end_date)
                    generic_report_pages.append(generic_report_page)

                    commercial_df = df.copy()
                    commercial_df.drop(
                        commercial_df.columns[generic_columns], axis=1, inplace=True)
                    
                    if (len(commercial_df.columns) == len(cleaned_columns)):
                        commercial_df.columns = cleaned_columns

                    commercial_report_page = self.parse_report(
                        commercial_df, name, start_date, end_date)
                    commercial_report_pages.append(
                        commercial_report_page)

                else:
                    single_report_page = self.parse_report(
                        df, name, start_date, end_date)
                    single_report_pages.append(single_report_page)

            pdf.close()

        if (len(generic_report_pages) > 1):
            pd.concat(generic_report_pages).to_csv(
                generic_file_output, index=False)

        if (len(commercial_report_pages) > 1):
            pd.concat(commercial_report_pages).to_csv(
                commercial_file_output, index=False)

        if (len(single_report_pages) > 1):
            pd.concat(single_report_pages).to_csv(file_output, index=False)

        return file_output

    def parse_report(self, df, name, start_date, end_date):
        items = pd.DataFrame(data=None, columns=['id', 'file_id', 'medication_name', 'dosage',
                                                 'maker', 'unit', 'vendor', 'price', 'currency',
                                                 'start_date', 'end_date'])

        # read pivoted (product x vendor) data
        for index, row in df.iterrows():
            medication_name = str(row[0]).strip()
            dosage = str(row[1]).strip()
            maker = str(row[2]).strip()
            unit = str(row[3]).strip()

            if (not medication_name and not dosage and not maker and not unit):
                continue

            for (label, contents) in df[df.columns[4:]].iteritems():
                value = contents.at[index]
                price = Price.fromstring(str(value))
                if not price.amount:
                    continue

                vendor = re.sub(
                    r'Unnamed:\s\d{1,2}_level_\d{1,2}', '', label)

                item = {
                    'id': uuid.uuid4(),
                    'file_id': name,
                    'medication_name': medication_name,
                    'dosage': dosage,
                    'maker': maker,
                    'unit': unit,
                    'vendor': vendor,
                    'price': price.amount,
                    'currency': 'DOP',
                    'start_date': start_date,
                    'end_date': end_date
                }

                items = items.append(item, ignore_index=True)

        return items
