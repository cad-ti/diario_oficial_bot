import re
from datetime import date, datetime as dt
import dateparser 

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider

from scrapy import Request


class RjPatyDoAlferesSpider(BaseGazetteSpider):
    name = "rj_paty_do_alferes"
    TERRITORY_ID = "3303856"
    allowed_domains = ["patydoalferes.rj.gov.br"]
    
    start_urls = ["https://patydoalferes.rj.gov.br/diario-oficial/"] 
    start_date = date(2009, 1, 1)

    def parse(self, response):

        all_diario_links = response.xpath("//ul//a[@class='bold' and @title]")

        for link in all_diario_links:
            
            title_attr = link.xpath("./@title").get()
            download_url_relative = link.xpath("./@href").get()
            
            edition_match = re.search(r"D\.O\.\s*(\d+)", title_attr)
            edition_number = edition_match.group(1) if edition_match else None
            
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', title_attr)
            raw_date_str = date_match.group(1) if date_match else None
  
            try:
                date_obj = dateparser.parse(
                    raw_date_str.strip(), 
                    date_formats=['%d/%m/%Y', '%m/%d/%Y'], 
                    languages=['pt'] 
                )
                
                
                gazette_date = date_obj.date()
                
            except Exception:
                continue
            
            if gazette_date > self.end_date:
                continue
            
            if gazette_date < self.start_date:
                continue 

            file_url = response.urljoin(download_url_relative)
            is_extra_edition = "Esp" in title_attr or "ESP" in title_attr.upper()
            
            yield Gazette(
                date=gazette_date,
                edition_number=edition_number,
                file_urls=[file_url],
                is_extra_edition=is_extra_edition,
                power="executive",
            )
        
