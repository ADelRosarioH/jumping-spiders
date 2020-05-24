# -*- coding: utf-8 -*-
import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from food_products.items import BasicBasketsItem


class BasicBasketsSpider(Spider):
    name = 'basic_baskets'

    custom_settings = {
        'FILES_STORE': 's3://jumping-spiders/food_products/basic_baskets/',
        'ITEM_PIPELINES': {
            'food_products.pipelines.BasicBasketsAvoidPdfsDuplicatesPipeline': 100,
            'food_products.pipelines.BasicBasketsPdfsToS3Pipeline': 200,
            'food_products.pipelines.BasicBasketsPdfsIndexingPipeline': 300,
        },
    }

    def __init__(self, connection_string=None, *args, **kwargs):
        super(BasicBasketsSpider, self).__init__(*args, **kwargs)
        self.connection_string = connection_string

    def start_requests(self):
        yield scrapy.Request(self.start_url)

    def parse(self, response):
        item = BasicBasketsItem()
        item['file_urls'] = response.css(
            'div.filetitle a::attr(href)').getall()
        return item
