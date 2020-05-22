# -*- coding: utf-8 -*-
import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from food_products.items import BasicBasketsItem


class BasicBasketsSpider(CrawlSpider):
    name = 'basic_baskets'
    allowed_domains = ['']
    start_urls = [os.getenv('START_URL')]

    rules = (
        Rule(LinkExtractor(), callback='parse', follow=True),
    )

    def parse(self, response):
        item = BasicBasketsItem()
        item["file_urls"] = response.css(
            'div.filetitle a::attr(href)').getall()
        return item
