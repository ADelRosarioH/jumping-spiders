import scrapy
from scrapy.selector import Selector
from jumping_spiders.items import FlowersItem
from datetime import date


class FlowersSpider(scrapy.Spider):
    name = 'flowers'

    custom_settings = {
        'FEEDS': {
            '/jumping-spiders/flowers/%(name)s-%(time)s.csv': {
                'format': 'csv',
                'fields': [
                    'description',
                    'unit',
                    'vendor',
                    'price',
                    'currency',
                    'last_published_at',
                    'last_updated_at',
                ],
                'encoding': 'utf-8',
            },
        },
    }

    def start_requests(self):
        start_urls = [
            'http://proconsumidor.gob.do/precios-de-flores.php'
        ]
        return [scrapy.Request(url) for url in start_urls]

    def parse(self, response):
        item = FlowersItem()

        last_updated_at = response.css(
            'div.container div.impre p::text').get().strip()

        def get_text(td):
            text = Selector(text=td).css(
                'td::text').get()
            if text:
                return text.strip()
            return ''

        for tr in response.css('div#productos div.impre center table.table-striped tr').getall():
            tds = Selector(text=tr).css('td').getall()

            item['vendor'] = get_text(tds[0])
            item['description'] = get_text(tds[1])
            item['unit'] = get_text(tds[2])
            item['price'] = get_text(tds[3])
            item['last_published_at'] = last_updated_at
            item['last_updated_at'] = date.today()

            yield item
