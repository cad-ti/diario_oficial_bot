from datetime import date

from diario_oficial_bot.spiders.base.ptio import BasePtioSpider


class RjArealSpider(BasePtioSpider):
    name = "rj_areal"
    TERRITORY_ID = "3300225"
    BASE_URL = "http://rj.portaldatransparencia.com.br/prefeitura/areal/"
    start_date = date(2006, 8, 1)
