import re
from datetime import date
from datetime import datetime
from scrapy import Request
from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider
 
class RjEstadoMpSpider(BaseGazetteSpider):
    name = "rj_estado_mp"
    TERRITORY_ID = "3399991"
    allowed_domains = ["www.mprj.mp.br"]
    start_urls = ["https://www.mprj.mp.br/busca?p_p_id=br_mp_mprj_internet_busca_web_BuscaPortlet&_br_mp_mprj_internet_busca_web_BuscaPortlet_filtro_param=doerj&_br_mp_mprj_internet_busca_web_BuscaPortlet_cur=1"]
    start_date = date(2012, 1, 2)
 
    def parse(self, response):
        data = response.css('div.content-card a')
        for edition in data:
            edition_date_text = edition.css('h3::text').get()
            edition_date_text = edition_date_text.replace(".", "/").strip()
            match_date = re.search(r'\d{2}/\d{2}/\d{4}', edition_date_text)
            
            try:
                edition_date = datetime.strptime(match_date.group(), "%d/%m/%Y").date()
            except:
                continue
            
            if edition_date > self.end_date:
                continue
            if edition_date < self.start_date:
                return
            
            edition_url = edition.css('::attr(href)').get()
            edition_url = "https://" + self.allowed_domains[0] + edition_url
            edition_number_text = edition.css('div.span-res-busca::text').get()
            
            try:
                edition_number = re.search(r'Edição nº ([\d.]+)', edition_number_text)
            except:
                continue
            if edition_number:
                edition_number = edition_number.group(1).replace('.', '')
                
            yield Gazette(
                date=edition_date,
                edition_number=edition_number,
                is_extra_edition=False,
                file_urls=[edition_url],
                power="executive",
            )
            
        current_url = response.url
        match = re.search(r'_br_mp_mprj_internet_busca_web_BuscaPortlet_cur=(\d+)', current_url)
        if match:
            current_page = int(match.group(1))
            next_page = re.sub(
                r'_br_mp_mprj_internet_busca_web_BuscaPortlet_cur=\d+',
                f'_br_mp_mprj_internet_busca_web_BuscaPortlet_cur={current_page+1}',
                current_url
            )
            yield Request(url=next_page)