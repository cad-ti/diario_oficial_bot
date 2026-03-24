import re
from datetime import date, datetime as dt

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider

from scrapy import Request

class RjPinheiralSpider(BaseGazetteSpider):
    name = "rj_pinheiral"
    TERRITORY_ID = "3303955"  
    allowed_domains = ["pinheiral.rj.gov.br"]
    
    start_urls = ["https://pinheiral.rj.gov.br/comunicacao/assessoria-de-comunicacao/informativos-oficiais/"] 
    start_date = date(2016, 1, 1)

    def parse(self, response):
        all_diario_blocks = response.xpath("//article[contains(@class, 'wow')]")
        
        for block in all_diario_blocks:
            
            title_link = block.xpath("./div/h3/a")
            date_span = block.xpath(".//span[@class='post-on hit-count has-dot' and @title='Data do Informativo']")
            
            title_text = title_link.xpath("./text()").get()
            raw_date_str = date_span.xpath("./text()").get()
            download_url_relative = title_link.xpath("./@href").get()

            edition_match = re.search(r"Nº\s*(\d+)", title_text)
            edition_number = edition_match.group(1) if edition_match else None
            
            gazette_date = dt.strptime(raw_date_str.strip(), "%d/%m/%Y").date()


            if gazette_date > self.end_date:
                continue
            
            if gazette_date < self.start_date:
                return 

            file_url = response.urljoin(download_url_relative)
            
            yield Gazette(
                date=gazette_date,
                edition_number=edition_number,
                file_urls=[file_url],
                is_extra_edition=False,
                power="executive",
            )

        next_page_relative = response.xpath(
            "//ul[@class='pagination justify-content-start']//a[i[contains(@class, 'fa-angle-right')]]/@href"
        ).get()

        if next_page_relative:
            next_page_url = response.urljoin(next_page_relative)
            
            yield Request(next_page_url, callback=self.parse)
        