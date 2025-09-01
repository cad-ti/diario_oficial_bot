from datetime import date

from diario_oficial_bot.spiders.base.ptio import BasePtioSpider


class RjSapucaiaSpider(BasePtioSpider):
    name = "rj_sapucaia"
    TERRITORY_ID = "3305406"
    BASE_URL = "http://rj.portaldatransparencia.com.br/prefeitura/sapucaia/"
    start_date = date(2019, 1, 16)
