from datetime import date, datetime

from scrapy import Request

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider


class RjArraialdoCaboSpider(BaseGazetteSpider):
    TERRITORY_ID = "3300258"
    name = "rj_arraial_do_cabo"
    allowed_domains = ["arraial.rj.gov.br"]
    start_urls = ["https://www.arraial.rj.gov.br/diariooficial"]
    start_date = date(2019, 4, 11)

    def parse(self, response):
        for entry in response.css('div[id="boxDiaries"] div.col-md-4'):
            edition = entry.css("div.card-header::text").re_first( r"(\d+)\s*/\s*\d{4}")
            file_url = entry.css('a[role="button"]::attr(href)').get()
            publish_date = entry.css("div.card-body p::text").re_first(r"\d{2}/\d{2}/\d{4}")
            publish_date = datetime.strptime(publish_date, "%d/%m/%Y").date()
            is_extra = entry.css('div.card-body p').getall()
            is_extra = len(is_extra) == 3

            if self.start_date <= publish_date <= self.end_date:
                yield Gazette(
                    date=publish_date,
                    file_urls=[response.urljoin(file_url)],
                    edition_number=edition,
                    is_extra_edition=is_extra,
                    power="executive",
                )

        next_page = response.css('ul.pagination.flex-wrap a::attr(href)').getall()[-1]
        if next_page and publish_date > self.start_date:
            yield Request(response.urljoin(next_page))
