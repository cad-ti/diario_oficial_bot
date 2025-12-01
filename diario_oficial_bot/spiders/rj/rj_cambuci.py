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
        for row in response.xpath("//table[contains(@class, 'table-striped')]/tbody/tr"):
            
            title_text = row.xpath("./td[1]/text()").get()

            edition_number = re.search(r"(\d+)", title_text).group(1) if re.search(r"(\d+)", title_text) else None

            raw_date = row.xpath("./td[2]/center/text()").get()
            
            gazette_date = dt.strptime(raw_date.strip(), "%d/%m/%Y").date()
            
            if gazette_date > self.end_date:
                continue

            if gazette_date < self.start_date:
                return 

            download_url_relative = row.xpath("./td[3]/center/a[1]/@href").get()
            
            file_url = response.urljoin(download_url_relative)

            yield Gazette(
                date=gazette_date,
                edition_number=edition_number,
                file_urls=[file_url],
                is_extra_edition=False, 
                power="executive",
            )

        current_page_li = response.xpath("//ul[@class='pagination justify-content-end']/li[contains(@class, 'active')]")
        
        next_page_path = current_page_li.xpath("./following-sibling::li/a[contains(@href, 'exibir')]/@href").get()
        
        if not next_page_path:
             next_page_path = response.xpath("//ul[@class='pagination justify-content-end']//a[contains(text(), '»')]/@href").get()

        if next_page_path:
            next_page_url = response.urljoin(next_page_path)
            yield Request(next_page_url, callback=self.parse)