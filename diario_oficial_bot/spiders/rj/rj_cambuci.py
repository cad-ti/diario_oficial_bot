import re
from datetime import date, datetime as dt
from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider
from scrapy import Request

class RjCambuciSpider(BaseGazetteSpider):
    name = "rj_cambuci"
    TERRITORY_ID = "3300902" 
    allowed_domains = ["prefeituradecambuci.rj.gov.br"]
    start_urls = ["https://prefeituradecambuci.rj.gov.br/transparencia/exibir/53/0/1/diario-oficial-eletronico"] 
    start_date = date(2017, 1, 1)

    def parse(self, response):
        rows = response.xpath("//table[contains(@class, 'table-striped')]/tbody/tr")
        
        for row in rows:
            title_text = row.xpath("./td[1]/text()").get()
            if not title_text:
                continue

            link_node = row.xpath("./td[3]//a[1]")
            href = link_node.xpath("./@href").get()
            icon_svg = link_node.xpath(".//*[local-name()='svg']/@data-icon").get()

            if icon_svg == "folder-open" or (href and "exibir" in href and not href.endswith(".pdf")):
                yield Request(
                    response.urljoin(href), 
                    callback=self.parse, 
                    priority=10
                )
                continue

            raw_date = row.xpath("./td[2]/center/text()").get()
            if not raw_date or not raw_date.strip():
                continue

            try:
                gazette_date = dt.strptime(raw_date.strip(), "%d/%m/%Y").date()
            except ValueError:
                continue

            if gazette_date > self.end_date:
                continue
            if gazette_date < self.start_date:
                return 

            edition_number = re.search(r"(\d+)", title_text).group(1) if re.search(r"(\d+)", title_text) else None
            
            yield Gazette(
                date=gazette_date,
                edition_number=edition_number,
                file_urls=[response.urljoin(href)],
                is_extra_edition=False, 
                power="executive",
            )

        current_page_li = response.xpath("//ul[@class='pagination justify-content-end']/li[contains(@class, 'active')]")
        next_page_path = current_page_li.xpath("./following-sibling::li/a[contains(@href, 'exibir')]/@href").get()
        
        if not next_page_path:
             next_page_path = response.xpath("//ul[@class='pagination justify-content-end']//a[contains(text(), '»')]/@href").get()

        if next_page_path:
            yield Request(
                response.urljoin(next_page_path), 
                callback=self.parse, 
                priority=1
            )