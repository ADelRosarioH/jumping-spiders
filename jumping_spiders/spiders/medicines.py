# -*- coding: utf-8 -*-
import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from jumping_spiders.items import MedicinesItem
import pdb


class MedicinesSpider(Spider):
    name = 'medicines'

    custom_settings = {
        'FILES_STORE': '/jumping-spiders/medicines/',
        'ITEM_PIPELINES': {
            'jumping_spiders.pipelines.FileDownloadPipeline': 200,
            'jumping_spiders.pipelines.MedicinesPdfsToCsvsPipeline': 300,
        },
    }

    def start_requests(self):
        start_urls = [
            'https://proconsumidor.gob.do/monitoreos-farmacias-2017/'
        ]
        return [scrapy.Request(url) for url in start_urls]

    def parse(self, response):
        item = MedicinesItem()
        item['file_urls'] = response.css(
            'div.filetitle a::attr(href)').getall()
        return item
