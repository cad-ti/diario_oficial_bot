import re
from datetime import date
import dateparser
import scrapy

from diario_oficial_bot.items import Gazette
from diario_oficial_bot.spiders.base import BaseGazetteSpider


class RjItaperunaSpider(BaseGazetteSpider):
    name = "rj_itaperuna"
    TERRITORY_ID = "3302205"
    allowed_domains = ["itaperuna.rj.gov.br"]
    start_date = date(2019, 1, 1)

    start_urls = [
        "https://itaperuna.rj.gov.br/pmi/jornal-oficial-2022",
        "https://itaperuna.rj.gov.br/pmi/jornal-oficial-2022-1",
        "https://itaperuna.rj.gov.br/pmi/jornal-oficial-2021",
        "https://itaperuna.rj.gov.br/pmi/jornal-oficial-2020",
        "https://itaperuna.rj.gov.br/pmi/jornal-oficial-2019",
    ]

    CORRECT_BASE_URL = "https://itaperuna.rj.gov.br/pmi/"
    INCORRECT_BASE_URL = "https://itaperuna.rj.gov.br/"

    def parse(self, response):
        for row in response.xpath("//table//tr[./td/span[contains(text(), 'Edição')]]"):
            title = row.xpath("./td[1]/span/text()").get(default="").strip()
            date_str = row.xpath("./td[2]/span/text()").get(default="").strip()
            download_url_relative = row.xpath(".//a[contains(@href, '.pdf')]/@href").get()

            if not date_str or not download_url_relative:
                continue

            if download_url_relative.startswith(self.INCORRECT_BASE_URL) and '/pmi/' not in download_url_relative:
                file_url = download_url_relative.replace(self.INCORRECT_BASE_URL, self.CORRECT_BASE_URL, 1)
            else:
                file_url = response.urljoin(download_url_relative.strip())

            date_obj = dateparser.parse(date_str, languages=["pt"])
            if not date_obj:
                continue

            gazette_date = date_obj.date()

            if gazette_date > self.end_date:
                continue
            
            if gazette_date < self.start_date:
                return 

            match = re.search(r"Edição\s*(\d+)", title)
            edition_number = match.group(1) if match else None

            yield Gazette(
                date=gazette_date,
                edition_number=edition_number,
                file_urls=[file_url],
                is_extra_edition=False,
                power="executive",
                image_pdf=True
            )
