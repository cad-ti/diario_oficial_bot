from datetime import datetime as dt

from scrapy import Request

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider


class BaseMentorSpider(BaseGazetteSpider):
    
    def start_requests(self):
        domain = self.allowed_domains[0]
        url = f"https://{domain}/recurso/diario/lista"
        start_date_str = self.start_date.strftime("%Y-%m-%d")
        end_date_str = self.end_date.strftime("%Y-%m-%d")
        url = f"{url}?dataInicial={start_date_str}&dataFinal={end_date_str}"
        yield Request(url)

    def parse(self, response):
        for gazette in response.json():          
            domain = self.allowed_domains[0]
            url = f"https://{domain}/recurso/diario/editar/{gazette["codigo"]}"
            yield Request(
                url=url,
                callback=self.parse_gazette)
            
    def parse_gazette(self, response):
        gazette = response.json()
        gazette_date = dt.strptime(gazette[ "dataPublicacao"], "%Y-%m-%d").date()
        extra = gazette["tipo"] == "E"
        
        domain = self.allowed_domains[0]
        url = f"https://{domain}/diario/#/verificar/{gazette['hash']}"

        yield Gazette(
            date=gazette_date,
            edition_number=gazette["edicao"],
            is_extra_edition=extra,
            power="executive_legislative",
            _file_content = gazette["arquivoPdf"],
            _file_content_url = url,
        )
