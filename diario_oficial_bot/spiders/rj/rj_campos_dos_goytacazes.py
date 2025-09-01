import re
from datetime import date

from scrapy import Request

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider
from diario_oficial_bot.utils.extraction import get_date_from_text


class RjCampoDosGoytacazesSpider(BaseGazetteSpider):
    name = "rj_campos_dos_goytacazes"
    TERRITORY_ID = "3301009"
    allowed_domains = ["www.campos.rj.gov.br"]
    start_urls = ["https://www.campos.rj.gov.br/diario-oficial.php"]
    start_date = date(2013, 11, 1)

    def parse(self, response):
        # first element is an obs website header
        for element in response.css("ul.ul-licitacoes li")[1:]:
            gazette_data = element.css("h4::text").get()

            gazette_date = re.search(
                r"\d{1,2}[ de]*(\w)*[ de]*\d{4}", gazette_data, re.I
            )
            gazette_date = gazette_date.group() if gazette_date else None

            date = get_date_from_text(gazette_date)
            if date is None:
                self.logger.warning(
                    f"Date inexistent or unable to parse date in {gazette_data} from {response.url}"
                )
                continue
            elif date > self.end_date:
                continue
            elif date < self.start_date:
                return

            edition_number = re.search(r"edição.*\s(\d+)", gazette_data, re.IGNORECASE)
            edition_number = edition_number.group(1) if edition_number else ""

            path_to_gazette = element.css("a::attr(href)").get().strip()
            # From November 17th, 2017 and backwards the path to the gazette PDF
            # is relative.
            if path_to_gazette.startswith("up/diario_oficial.php"):
                path_to_gazette = response.urljoin(path_to_gazette)

            is_extra_edition = bool(
                re.search(r"extra|supl|revis", gazette_data, re.IGNORECASE)
            )

            yield Gazette(
                date=date,
                edition_number=edition_number,
                is_extra_edition=is_extra_edition,
                file_urls=[path_to_gazette],
                power="executive",
            )

        next_url = (
            response.css(".pagination")
            .xpath("//a[contains(text(), 'Proxima')]/@href")
            .get()
        )
        if next_url:
            yield Request(response.urljoin(next_url))
