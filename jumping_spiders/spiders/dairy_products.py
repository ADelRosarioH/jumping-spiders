import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from jumping_spiders.items import DairyProductsItem
from pathlib import Path

class DairyProductsSpider(scrapy.Spider):
    name = 'dairy_products'

    custom_settings = {
        'FILES_STORE': Path.home().joinpath('jumping-spiders/dairy_products/'),
        'ITEM_PIPELINES': {
            'jumping_spiders.pipelines.FileDownloadPipeline': 200,
            'jumping_spiders.pipelines.BasicBasketsPdfsToCsvsPipeline': 300,
        },
    }

    def start_requests(self):
        start_urls = [
            # 'https://proconsumidor.gob.do/monitoreos-diferentes-tipos-de-leches-2017/',
            # 'https://proconsumidor.gob.do/monitoreos-diferentes-tipos-de-leches-2018/',
            # 'https://proconsumidor.gob.do/monitoreos-diferentes-tipos-de-leches-2019/',
            'https://proconsumidor.gob.do/monitoreos-diferentes-tipos-de-leches-2020/'
        ]
        return [scrapy.Request(url) for url in start_urls]

    def parse(self, response):
        item = DairyProductsItem()
        item['file_urls'] = response.css(
            'div.filetitle a::attr(href)').getall()
        return item
