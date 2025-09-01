from datetime import date
import datetime as dt
import scrapy
import re
import base64

from scrapy.selector import Selector
from diario_oficial_bot.spiders.base import BaseGazetteSpider


def b64e(s):
    return base64.b64encode(s.encode()).decode()

class BaseDoerjSpider(BaseGazetteSpider):
    allowed_domains = ["ioerj.com.br"]
    start_urls = ["https://www.ioerj.com.br/"]
    start_date = date(2019, 1, 2)

    def parse(self, response):
        parsing_date = self.end_date

        while parsing_date >= self.start_date:
            start_url = "https://www.ioerj.com.br/portal/modules/conteudoonline/do_seleciona_edicao.php?data={}"
            yield scrapy.Request(
                start_url.format(b64e(parsing_date.strftime('%Y%m%d'))),
                callback=self.captura_doerj,
                cb_kwargs={"parsing_date": parsing_date},
            )
            parsing_date = parsing_date - dt.timedelta(days=1)

    def captura_doerj(self, response, parsing_date):
        if response.status == 200:
            # Substitui BeautifulSoup por XPath
            cadernos = response.xpath('//a[@id="cor-texto"]')
            for caderno in cadernos:
                nome_caderno = caderno.xpath('normalize-space(text())').get()
                href = caderno.xpath('@href').get()

                if href:
                    id_caderno = href.split('session=')[1]
                    url_caderno = f'https://www.ioerj.com.br/portal/modules/conteudoonline/mostra_edicao.php?session={id_caderno}'
                    yield scrapy.Request(
                        url_caderno,
                        method="GET",
                        callback=self.captura_caderno,
                        cb_kwargs={"nome_caderno": nome_caderno, "data_caderno": parsing_date},
                    )

    def parse_pdf_id(self, html_string):
        sel = Selector(text=html_string)
        scripts = sel.xpath('//script[@type="text/javascript"]/text()').getall()

        regex_declaracao_variavel = r"(?m)^var\s+([\w_\$]+)\s*=\s*(.*?)(?:;|\n|$)"
        for conteudo_script in scripts:
            conteudo_script = conteudo_script.strip()
            match = re.search(regex_declaracao_variavel, conteudo_script)

            if match:
                nome_variavel, valor_variavel = match.groups()
                if nome_variavel == 'pd':
                    pdf_id = valor_variavel.replace('"', '')
                    pdf_id = pdf_id[:12] + 'P' + pdf_id[12:]
                    return pdf_id
        return None
