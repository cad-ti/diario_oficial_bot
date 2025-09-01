from datetime import date

from diario_oficial_bot.spiders.base.rgsites import BaseRgSitesSpider


class RjCantagaloSpider(BaseRgSitesSpider):
    name = "rj_cantagalo"
    TERRITORY_ID = "3301108"
    allowed_domains = ["www.cantagalo.rj.gov.br"]
    BASE_URL = "https://www.cantagalo.rj.gov.br/transparencia/diario-oficial"
    start_date = date(2018, 3, 26)
