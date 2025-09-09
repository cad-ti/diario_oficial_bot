from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base.doerj import BaseDoerjSpider

class RJERJSpider(BaseDoerjSpider):
    name="rj_estado_tce"
    TERRITORY_ID="3399993"
    poder="Tribunal de Contas"
    power="legislative"

