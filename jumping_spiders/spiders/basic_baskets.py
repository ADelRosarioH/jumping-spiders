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
        'FILES_STORE': '/jumping-spiders/basic_baskets/',
        'ITEM_PIPELINES': {
            'jumping_spiders.pipelines.FileDownloadPipeline': 200,
            'jumping_spiders.pipelines.BasicBasketsPdfsToCsvsPipeline': 300,
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
