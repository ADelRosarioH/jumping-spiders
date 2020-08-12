# -*- coding: utf-8 -*-
import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from jumping_spiders.items import BasicBasketsItem
from pathlib import Path

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
        start_urls = [
            # 'https://proconsumidor.gob.do/sondeos-de-canasta-basica-2017/',
            # 'https://proconsumidor.gob.do/sondeos-de-canasta-basica-2018/',
            # 'https://proconsumidor.gob.do/sondeos-de-canasta-basica-2019/',
            'https://proconsumidor.gob.do/sondeos-de-canasta-basica-2020/'
        ]
        return [scrapy.Request(url) for url in start_urls]

    def parse(self, response):
        item = BasicBasketsItem()
        item['file_urls'] = response.css(
            'div.filetitle a::attr(href)').getall()
        return item
