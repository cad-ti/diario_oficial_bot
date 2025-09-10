from datetime import date, datetime as dt

from diario_oficial_bot.spiders.base.mentor import BaseMentorSpider


class RjItatiaiaSpider(BaseMentorSpider):
    name = "rj_teresopolis"
    allowed_domains = ["atos.teresopolis.rj.gov.br"]
    TERRITORY_ID = "3302254"
    start_date = date(2016, 7, 22)
