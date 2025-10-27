import re
from datetime import date, datetime as dt
import dateparser

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider

from scrapy import Request


class RjPiraiSpider(BaseGazetteSpider):
    name = "rj_pirai"
    TERRITORY_ID = "3304003"  
    allowed_domains = ["transparencia.pirai.rj.gov.br", "pirai.rj.gov.br"]
    
    start_urls = [
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2025",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2024",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2023",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2022",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2021",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2020",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2019",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2018",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2017",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2016",
        "https://transparencia.pirai.rj.gov.br/boletins-informativos-2015",
    ] 
    start_date = date(2015, 1, 1)

    def parse(self, response):
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

            
            date_obj = dateparser.parse(
                    raw_date_str.strip(), 
                    languages=["pt"],
                    settings={'DATE_ORDER': 'DMY'} 
                )
            gazette_date = date_obj.date()
            

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