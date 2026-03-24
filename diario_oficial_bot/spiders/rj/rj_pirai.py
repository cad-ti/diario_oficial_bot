import re
from datetime import date, datetime as dt
import dateparser

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider
from diario_oficial_bot.utils.extraction import get_date_from_text

from scrapy import Request


class RjPiraiSpider(BaseGazetteSpider):
    name = "rj_pirai"
    TERRITORY_ID = "3304003"  
    allowed_domains = ["transparencia.pirai.rj.gov.br", "pirai.rj.gov.br"]
    start_urls = ["https://transparencia.pirai.rj.gov.br/boletins-informativos"]
    
    def _parse(self, response):
        year_links = response.xpath("//a[contains(@href, '/boletins-informativos-')]")
        for link in year_links:
            href = link.xpath("./@href").get()
            
            if not href:
                continue

            year_match = re.search(r'(\d{4})', href)
            if not year_match:
                continue
                
            year = int(year_match.group(1))

            if self.start_date.year <= year <= self.end_date.year:
                yield response.follow(href, callback=self.parse_gazettes)
    
    def parse_gazettes(self, response):
        all_diario_links = response.xpath(
            "//p/a[contains(@href, '.pdf')]"
        )

        for link in all_diario_links:
            
            text_content = link.xpath("./text()").get()
            download_url_relative = link.xpath("./@href").get()
            
            if not text_content or not download_url_relative:
                continue
            
            text_content = text_content.strip()

            edition_number_match = re.search(r'(\d+)', text_content)
            edition_number = edition_number_match.group(1) if edition_number_match else None
            
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text_content)
            raw_date_str = date_match.group(1) if date_match else None
            
            if not edition_number or not raw_date_str:
                continue

            gazette_date = get_date_from_text(raw_date_str)
            

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