from datetime import date
import scrapy
from parsel import Selector

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider


class RjPatyDoAlferesSpider(BaseGazetteSpider):
    name = "rj_paty_do_alferes"
    TERRITORY_ID = "3303856"
    allowed_domains = ["patydoalferes.rj.gov.br"]
    start_date = date(2009, 1, 1)

    def start_requests(self):
        yield scrapy.Request(
            url="https://patydoalferes.rj.gov.br/",
            callback=self.make_requests_for_years,
            headers={"User-Agent": "Mozilla/5.0"},
        )

    def make_requests_for_years(self, response):
        url = "https://patydoalferes.rj.gov.br/wp-admin/admin-ajax.php"

        for year in range(self.start_date.year, date.today().year + 1):
            yield scrapy.FormRequest(
                url=url,
                formdata={
                    "action": "pdo_old_list_rows",
                    "dirrel": str(year),
                },
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://patydoalferes.rj.gov.br/",
                    "X-Requested-With": "XMLHttpRequest",
                },
                #cb_kwargs={"year": year}
            )

    def parse(self, response):
        data = response.json()
        html = data.get("data", {}).get("html", "")

        selector = Selector(text=html)

        for tr in selector.xpath("//tr"):
            url = tr.xpath("./@data-url").get()
            date_str = tr.xpath("./@data-dateiso").get()
            edition = tr.xpath("./@data-edicao").get()  
            complemento = tr.xpath("./td[3]/text()").get()
            
            gazette_date = date.fromisoformat(date_str)

            if gazette_date > self.end_date:
                continue
            if gazette_date < self.start_date:
                return
            
            is_extra_edition = bool(complemento and complemento.strip())
            #NAO ESTA FUNCIONANDO O EXTRA EDITION
            yield Gazette(
                date=gazette_date,
                file_urls=[url],
                edition_number=edition,
                is_extra_edition=is_extra_edition,
                power="executive_legislative",
            )