import re
import json
import scrapy
from datetime import date, datetime

from scrapy import Request

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider
from diario_oficial_bot.utils.dates import yearly_sequence
from diario_oficial_bot.utils.extraction import get_date_from_text


class RjBarraMansaSpider(BaseGazetteSpider):
    TERRITORY_ID = "3300407"
    allowed_domains = ["barramansa.rj.gov.br"]
    name = "rj_barra_mansa"
    start_urls = ["https://portaltransparencia.barramansa.rj.gov.br/boletim-oficial/"]
    start_date = date(2017, 1, 3)
    ajax_url = "https://portaltransparencia.barramansa.rj.gov.br/wp-admin/admin-ajax.php"
    page_size = 20
    draw = 1

    def start_requests(self):
        yield scrapy.FormRequest(
            url=self.ajax_url,
            formdata=self._payload(start=0, draw = 1),
            callback=self.parse,
            meta={"start": 0}
        )

    def _payload(self, start, draw):
        return {
            "draw": str(draw),
            "start": str(start),
            "length": str(self.page_size),

            "order[0][column]": "2",
            "order[0][dir]": "desc",
            "action": "wpdm_all_packages_data",
            "params[cols]": "title,file_count,download_count|categories|publish_date|download_link",
            "params[categories]": "boletim-oficial",
            "params[order_by]": "publish_date",
            "params[order]": "DESC",
            "cfurl": "https://portaltransparencia.barramansa.rj.gov.br/boletim-oficial/",
        }

    def parse(self, response):
        data = json.loads(response.text)

        for row in data.get("data", []):
            gazette_date = row["publish_date_raw"]
            gazette_date = datetime.strptime(gazette_date, "%Y-%m-%d").date()

            if gazette_date < self.start_date:
                return

            if self.end_date < gazette_date:
                continue

            path_to_gazette = re.search(r'data-downloadurl="([^"]+)"', row["download_link"])

            if path_to_gazette:
                path_to_gazette = path_to_gazette.group(1).replace('\\/', '/')

            gazette_edition = list(row["files"].values())[0]
            edition_match = re.search(r"BO\s*-\s*BM\s*-\s*(\d+)", gazette_edition)
            if edition_match == None:
                continue
            gazette_edition = edition_match.group(1) if edition_match else None
            is_extra = "extra" in gazette_edition
            yield Gazette(
                date=gazette_date,
                file_urls=[path_to_gazette],
                is_extra_edition=is_extra,
                power="executive",
                edition_number=gazette_edition,
            )

        if not data["data"]:
            return
        start = response.meta["start"] + self.page_size
        self.draw += 1
        yield scrapy.FormRequest(
            url=self.ajax_url,
            formdata=self._payload(start, self.draw),
            callback=self.parse,
            meta={"start": start}
        )