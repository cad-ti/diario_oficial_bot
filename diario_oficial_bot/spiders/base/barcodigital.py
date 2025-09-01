from datetime import datetime

from scrapy import Request
from scrapy.exceptions import NotConfigured

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider
from diario_oficial_bot.utils.dates import monthly_sequence


class BaseBarcoDigitalSpider(BaseGazetteSpider):
    EDITION_TYPE_NORMAL = 1
    EDITION_TYPE_EXTRA = 2
    EDITION_TYPE_SUPPLEMENT = 3

    allowed_domains = ["barcodigital.com.br"]

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "base_url"):
            raise NotConfigured("Please set a value for `base_url`")

        super(BaseBarcoDigitalSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for date in monthly_sequence(self.start_date, self.end_date):
            url = f"{self.base_url}/api/publico/diario/calendario?mes={date.month}&ano={date.year}"
            yield Request(url)

    def parse(self, response):
        for documents in response.json().values():
            for document in documents:
                document_date = datetime.strptime(
                    document.get("data"), "%Y-%m-%d"
                ).date()

                if document_date > self.end_date:
                    continue
                elif document_date < self.start_date:
                    return

                yield Gazette(
                    date=document_date,
                    edition_number=document.get("edicao"),
                    is_extra_edition=document.get("tipo_edicao_id")
                    != self.EDITION_TYPE_NORMAL,
                    file_urls=[f"{self.base_url}/arquivo/{document.get('url')}"],
                    power="executive",
                )
