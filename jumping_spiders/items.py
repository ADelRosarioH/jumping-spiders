# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BasicBasketsItem(scrapy.Item):
    file_urls = scrapy.Field()
    file_paths = scrapy.Field()
    file_outputs = scrapy.Field()


class DairyProductsItem(scrapy.Item):
    file_urls = scrapy.Field()
    file_paths = scrapy.Field()
    file_outputs = scrapy.Field()


class HardwareProductsItem(scrapy.Item):
    file_urls = scrapy.Field()
    file_paths = scrapy.Field()
    file_outputs = scrapy.Field()


class TextBooksItem(scrapy.Item):
    file_urls = scrapy.Field()
    file_paths = scrapy.Field()
    file_outputs = scrapy.Field()


class TransportationFeesItem(scrapy.Item):
    province = scrapy.Field()
    town = scrapy.Field()
    route = scrapy.Field()
    company = scrapy.Field()
    phone_number = scrapy.Field()
    representative = scrapy.Field()
    stop = scrapy.Field()
    line = scrapy.Field()
    cost = scrapy.Field()
    last_updated_at = scrapy.Field()
    last_published_at = scrapy.Field()


class FlowersItem(scrapy.Item):
    vendor = scrapy.Field()
    description = scrapy.Field()
    unit = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    last_updated_at = scrapy.Field()
    last_published_at = scrapy.Field()
    

class MedicinesItem(scrapy.Item):
    file_urls = scrapy.Field()
    file_paths = scrapy.Field()
    file_outputs = scrapy.Field()
