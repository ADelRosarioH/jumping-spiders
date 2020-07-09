# -*- coding: utf-8 -*-
import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from jumping_spiders.items import BasicBasketsItem
import pdb


class BasicBasketsSpider(Spider):
    name = 'basic_baskets'

    custom_settings = {
        'FILES_STORE': '/tmp/',
        'FILES_STORE_S3': 's3://jumping-spiders/jumping_spiders/basic_baskets/',
        'ITEM_PIPELINES': {
            'jumping_spiders.pipelines.BasicBasketsDuplicatesFilterPipeline': 100,
            'jumping_spiders.pipelines.BasicBasketsPdfsDownloadPipeline': 200,
            'jumping_spiders.pipelines.BasicBasketsPdfsToCsvsPipeline': 300,
            'jumping_spiders.pipelines.BasicBasketsFilesUploadPipeline': 400,
            'jumping_spiders.pipelines.BasicBasketsPdfsIndexingPipeline': 500,
        },
        'DATABASE_SETTINGS': {
            'host': 'jumping-spiders.czko62ocualm.us-east-2.rds.amazonaws.com',
            'port': 5432,
            'username': 'postgres',
            'password': '50F2AUiw5vvIMwkZX90a',
            'database': 'jumping_spiders',
        },
    }

    def start_requests(self):
        start_urls = self.start_urls.split(',')
        return [scrapy.Request(url) for url in start_urls]

    def parse(self, response):
        item = BasicBasketsItem()
        item['file_urls'] = response.css(
            'div.filetitle a::attr(href)').getall()
        return item
