from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base.doerj import BaseDoerjSpider

class RJERJSpider(BaseDoerjSpider):
    name = "rj_estado_alerj"
    TERRITORY_ID = "3399992"

    def captura_caderno(self, response, nome_caderno, data_caderno):
        if response.status == 200:
            # parse_pdf_id agora usa apenas Scrapy
            pdf_id = self.parse_pdf_id(response.text)

            if pdf_id and 'Legislativo' in nome_caderno:
                download_url = f'https://www.ioerj.com.br/portal/modules/conteudoonline/mostra_edicao.php?k={pdf_id}'
                yield Gazette(
                    date=data_caderno,
                    file_urls=[download_url],
                    is_extra_edition=False,
                    power="legislative",
                )

