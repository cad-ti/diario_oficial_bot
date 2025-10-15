import re
from datetime import date, datetime as dt

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider

from scrapy import Request


class RjItaocaraSpider(BaseGazetteSpider):
    name = "rj_itaocara"
    TERRITORY_ID = "3302106"  
    allowed_domains = ["itaocara.rj.gov.br"]

    start_urls = ["https://www.itaocara.rj.gov.br/diario-oficial-eletronico"] 
    start_date = date(2017, 1, 1) 

    def parse(self, response):
        all_diario_rows = response.xpath(
            "//table[contains(@class, 'table-diario')]//tbody/tr"
        )

        for row in all_diario_rows:

            link_a = row.xpath("./td[@class='edicao']/a")
            download_a = row.xpath("./td[@class='download']/a")

            title_attr = link_a.xpath("./@title").get()
            raw_date_mobile = link_a.xpath("./span/text()").get()
            download_url_relative = download_a.xpath("./@href").get()

            raw_date = raw_date_mobile.strip().strip("()") 
            title_text = title_attr.strip() 

            gazette_date = dt.strptime(raw_date, "%d/%m/%Y").date()

            if gazette_date > self.end_date:
                continue

            if gazette_date < self.start_date:
                continue 

            edition_number_match = re.search(r"BIOPI\s*-\s*(\d+)", title_text)
            edition_number = edition_number_match.group(1) if edition_number_match else None

            is_extra_edition = "ADENDO" in title_text.upper() 

            file_url = response.urljoin(download_url_relative)

            yield Gazette(
                date=gazette_date,
                edition_number=edition_number,
                file_urls=[file_url],
                is_extra_edition=is_extra_edition,
                power="executive_legislative",
            )