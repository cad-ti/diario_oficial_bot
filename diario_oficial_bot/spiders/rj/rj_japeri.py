from datetime import datetime, date

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider


class RjJaperiSpider(BaseGazetteSpider):
    TERRITORY_ID = "3302270"
    name = "rj_japeri"
    allowed_domains = ["pmjaperi.geosiap.net.br"]
    start_date = date(2019, 7, 22)
    start_urls = [
        "https://pmjaperi.geosiap.net.br/portal-transparencia/api/default/publicacoes/publicacoes"
    ]

    def parse(self, response):
        for item in response.json()["publicacoes"]:
            if item["ds_publicacao_tipo"] != "DIÁRIO OFICIAL":
                continue
            
            edition_date = datetime.strptime(item["dt_publicacao"], "%Y-%m-%d").date()          
            if edition_date > self.end_date:
                continue
            if edition_date < self.start_date:
                return
            
            url = f"https://pmjaperi.geosiap.net.br/portal-transparencia/api/default/publicacoes/get_arquivo?id_publicacao={item['id_publicacao']}"
            
            yield Gazette(
                date=edition_date, 
                file_urls=[url], 
                is_extra_edition=False,
                power="executive"
            )
