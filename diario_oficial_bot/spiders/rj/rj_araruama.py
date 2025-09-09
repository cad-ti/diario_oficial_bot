import re

from datetime import date, datetime as dt

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider

from scrapy import Request


class RjSaquaremaSpider(BaseGazetteSpider):
    name = "rj_araruama"
    TERRITORY_ID = "3300209"
    allowed_domains = ["araruama.rj.gov.br"]
    start_urls = ["https://www.araruama.rj.gov.br/publicacoes/diario-oficial"]
    start_date = date(2017, 5, 12)

    def parse(self, response):
        for link in response.xpath("//*[@id='pubs']/li/a"):
            raw_date = link.xpath(".//span/text()").get().strip()[:10]
            date = dt.strptime(raw_date, "%d/%m/%Y").date()
            if date > self.end_date:
                continue
            if date < self.start_date:
                return
            
            gazette_text = link.xpath(".//div[@class='small content-pub']/text()").get()
            gazette_text = gazette_text.strip().replace(".", "")
            edition_number = re.search(r"Nº\s*(\d+)", gazette_text).group(1)

            gazette = {"date": date, "edition_number": edition_number}
            
            url = link.xpath(".//@href").get()
            yield Request(
                url=url,
                callback=self.parse_gazette,
                cb_kwargs={"gazette": gazette}
            )
        
        next_page_url = response.xpath('//a[@rel="next"]/@href').get()
        if next_page_url:
            yield Request(next_page_url)

    def parse_gazette(self, response, gazette):
        url = response.xpath("//a[@data-title='Clique para baixar']/@href").get()
        if url:
            yield Gazette(
                **gazette,
                file_urls=[url],
                power="executive",
                is_extra_edition=False
            )






