import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from jumping_spiders.items import TextBooksItem
from pathlib import Path

class TextBooksSpider(scrapy.Spider):
    name = 'text_books'

    custom_settings = {
        'FILES_STORE': '/jumping-spiders/text_books/',
        'ITEM_PIPELINES': {
            'jumping_spiders.pipelines.FileDownloadPipeline': 200,
            'jumping_spiders.pipelines.BasicBasketsPdfsToCsvsPipeline': 300,
        },
    }

    def start_requests(self):
        start_urls = [
            'https://proconsumidor.gob.do/monitoreo-de-libros-de-textos/'
        ]
        return [scrapy.Request(url) for url in start_urls]

    def parse(self, response):
        item = TextBooksItem()
        item['file_urls'] = response.css(
            'div.filetitle a::attr(href)').getall()
        return item
