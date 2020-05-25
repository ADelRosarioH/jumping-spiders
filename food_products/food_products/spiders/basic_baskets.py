# -*- coding: utf-8 -*-
import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from food_products.items import BasicBasketsItem
import pdb


class BasicBasketsSpider(Spider):
    name = 'basic_baskets'

    custom_settings = {
        'FILES_STORE': 's3://jumping-spiders/food_products/basic_baskets/',
        'ITEM_PIPELINES': {
            'food_products.pipelines.BasicBasketsAvoidPdfsDuplicatesPipeline': 100,
            'food_products.pipelines.BasicBasketsPdfsToS3Pipeline': 200,
            'food_products.pipelines.BasicBasketsPdfsIndexingPipeline': 300,
        },
        'DATABASE_SETTINGS': {
            'host': 'jumping-spiders.czko62ocualm.us-east-2.rds.amazonaws.com',
            'port': 5432,
            'username': 'postgres',
            'password': '50F2AUiw5vvIMwkZX90a',
            'database': 'food_products',
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
