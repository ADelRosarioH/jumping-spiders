# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
import scrapy
import hashlib
import mimetypes
from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem, NotConfigured
from scrapy.utils.python import to_bytes
from urllib.parse import urlparse
from food_products.utils.database import get_session


class BasicBasketsAvoidPdfsDuplicatesPipeline:

    def process_item(self, item, spider):
        settings = spider.settings['DATABASE_SETTINGS']
        session = get_session(**settings)

        file_urls = []

        for file_url in item['file_urls']:
            file_hash = hashlib.sha1(to_bytes(file_url)).hexdigest()
            result = session.execute(
                "SELECT 1 FROM basic_baskets_indexing WHERE file_hash = '{}' LIMIT 1".format(file_hash)).scalar()

            if not result:
                file_urls.append(file_url)

        item['file_urls'] = file_urls

        return item


class BasicBasketsPdfsToS3Pipeline(FilesPipeline):

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


class BasicBasketsPdfsIndexingPipeline:
    def process_item(self, item, spider):
        settings = spider.settings['DATABASE_SETTINGS']
        session = get_session(**settings)

        for (file_url, file_path) in zip(item['file_urls'], item['file_paths']):
            file_hash = hashlib.sha1(to_bytes(file_url)).hexdigest()
            file = {
                'file_hash': file_hash,
                'file_url': file_url,
                'file_path': file_path
            }
            session.execute("""INSERT INTO basic_baskets_indexing (file_hash, file_url, file_path) 
                VALUES (:file_hash, :file_url, :file_path)""", file)

        session.commit()

        return item
