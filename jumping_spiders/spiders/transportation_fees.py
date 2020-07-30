import scrapy
from scrapy.selector import Selector
from jumping_spiders.items import TransportationFeesItem


class TransportationFeesSpider(scrapy.Spider):
    name = 'transportation_fees'

    custom_settings = {
        'FEEDS': {
            '/jumping-spiders/transportation_fees/export.csv': {
                'format': 'csv',
                'fields': [
                    'province',
                    'town',
                    'route',
                    'company',
                    'phone_number',
                    'representative',
                    'stop',
                    'line',
                    'cost',
                    'last_updated_at',
                ],
                'encoding': 'utf-8',
            },
        },
    }

    def start_requests(self):
        start_urls = [
            'https://proconsumidor.gob.do/precio-de-pasajes-autobus.php'
        ]
        return [scrapy.Request(url) for url in start_urls]

    def parse(self, response):
        item = TransportationFeesItem()

        last_updated_at = response.css(
            'div.container div.impre div#fecha::text').get().strip()

        def get_text(td):
            text = Selector(text=td).css(
                'td::text').get()
            if text:
                return text.strip()
            return ''

        for tr in response.css('div#productos div.impre center table.table-striped tr').getall():
            tds = Selector(text=tr).css('td').getall()

            item['province'] = get_text(tds[0])
            item['town'] = get_text(tds[1])
            item['route'] = get_text(tds[2])
            item['company'] = get_text(tds[3])
            item['phone_number'] = get_text(tds[4])
            item['representative'] = get_text(tds[5])
            item['stop'] = get_text(tds[6])
            item['line'] = get_text(tds[7])
            item['cost'] = get_text(tds[8])
            item['last_updated_at'] = last_updated_at

            yield item
