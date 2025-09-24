import re
from datetime import date
from datetime import datetime
from scrapy import Request
import scrapy
from scrapy import Request
from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider
from diario_oficial_bot.utils.extraction import get_date_from_text
 
 
class RjEstadoMpSpider(BaseGazetteSpider):
    name = "rj_estado_mp"
    TERRITORY_ID = "3399991"
    allowed_domains = ["www.mprj.mp.br"]
    start_urls = ["https://www.mprj.mp.br/busca?p_p_id=br_mp_mprj_internet_busca_web_BuscaPortlet&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_br_mp_mprj_internet_busca_web_BuscaPortlet_periodo_param=todas&_br_mp_mprj_internet_busca_web_BuscaPortlet_order_param=desc&_br_mp_mprj_internet_busca_web_BuscaPortlet_filtro_param=doerj&_br_mp_mprj_internet_busca_web_BuscaPortlet_exibicao_param=card&_br_mp_mprj_internet_busca_web_BuscaPortlet_jspPage=%2Fhtml%2Fview.jsp&_br_mp_mprj_internet_busca_web_BuscaPortlet_revistas_param=todasRev&_br_mp_mprj_internet_busca_web_BuscaPortlet_delta=15&_br_mp_mprj_internet_busca_web_BuscaPortlet_keywords=&_br_mp_mprj_internet_busca_web_BuscaPortlet_advancedSearch=false&_br_mp_mprj_internet_busca_web_BuscaPortlet_andOperator=true&_br_mp_mprj_internet_busca_web_BuscaPortlet_resetCur=false&_br_mp_mprj_internet_busca_web_BuscaPortlet_cur=1"]
    start_date = date(2012, 1, 2)
 
    def parse(self, response):
        data = response.css('div.content-card a')
        for edition in data:
            edition_date_text = edition.css('h3::text').get()
            edition_date = re.search(r'\d{2}/\d{2}/\d{4}', edition_date_text)
            if not edition_date:
                edition_date = re.search(r'\d{2}\.\d{2}\.\d{4}', edition_date_text)
                edition_date_text = edition_date_text.replace(".", "/").strip()
            if edition_date:
                edition_date = edition_date.group()
                try:
                    edition_date = datetime.strptime(edition_date, "%d/%m/%Y").date()
                except:
                    continue
                if not self.start_date <= edition_date <= self.end_date:
                    if edition_date < self.start_date:
                        return
                    continue
            else:
                continue
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