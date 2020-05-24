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
import logging

from scrapy.pipelines.files import FilesPipeline
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
from scrapy.utils.python import to_bytes
from urllib.parse import urlparse
from io import StringIO
from price_parser import Price
from slugify import slugify
from .utils.dates import get_date_range_form_url
from .utils.database import get_engine

logger = logging.getLogger(__name__)


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
