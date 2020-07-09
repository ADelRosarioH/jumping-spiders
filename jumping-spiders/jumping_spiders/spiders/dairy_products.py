import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from jumping_spiders.items import DairyProductsItem
import pdb


class DairyProductsSpider(scrapy.Spider):
    name = 'dairy_products'

    custom_settings = {
        'FILES_STORE': '/tmp/dairy_products/',
        'ITEM_PIPELINES': {
            'jumping_spiders.pipelines.BasicBasketsPdfsDownloadPipeline': 200,
            'jumping_spiders.pipelines.BasicBasketsPdfsToCsvsPipeline': 300,
        },
    }

    def start_requests(self):
        start_urls = self.start_urls.split(',')
        return [scrapy.Request(url) for url in start_urls]

    def parse(self, response):
        item = DairyProductsItem()
        item['file_urls'] = response.css(
            'div.filetitle a::attr(href)').getall()
        return item
