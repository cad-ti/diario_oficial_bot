from datetime import datetime as dt, UTC
from pathlib import Path
from itemadapter import ItemAdapter
from scrapy.http import Request
from scrapy.http.request import NO_CALLBACK
from scrapy.pipelines.files import FilesPipeline
from scrapy.settings import Settings
import filetype


class DiarioOficialBotPipeline:
    def process_item(self, item, spider):
        item["territory_id"] = getattr(spider, "TERRITORY_ID")
        item["name"] = getattr(spider, "name")

        # Date manipulation to allow jsonschema to validate correctly
        item["date"] = str(item["date"])
        item["scraped_at"] = dt.now(UTC).isoformat("T") + "Z"

        return item

class DiarioOficialFilesPipeline(FilesPipeline):
    """Pipeline to download files described in file_urls or file_requests item fields.

    The main differences from the default FilesPipelines is that this pipeline:
        - organizes downloaded files differently (based on territory_id)
        - adds the file_requests item field to download files from request instances
        - allows a download_file_headers spider attribute to modify file_urls requests
    """

    DEFAULT_FILES_REQUESTS_FIELD = "file_requests"

    def __init__(self, store_uri, crawler, *args, **kwargs):
        # repassa crawler para o FilesPipeline
        super().__init__(store_uri, crawler=crawler, *args, **kwargs)

        settings = crawler.settings
        if isinstance(settings, dict) or settings is None:
            settings = Settings(settings)

        self.files_requests_field = settings.get(
            "FILES_REQUESTS_FIELD", self.DEFAULT_FILES_REQUESTS_FIELD
        )

    @classmethod
    def from_crawler(cls, crawler):
        store_uri = crawler.settings.get("FILES_STORE")
        return cls(store_uri, crawler)

    def get_media_requests(self, item, info):
        """Makes requests from urls and/or lets through ready requests."""
        urls = ItemAdapter(item).get(self.files_urls_field, [])
        download_file_headers = getattr(info.spider, "download_file_headers", {})
        yield from (
            Request(u, callback=NO_CALLBACK, headers=download_file_headers)
            for u in urls
        )

        requests = ItemAdapter(item).get(self.files_requests_field, [])
        yield from requests

    def item_completed(self, results, item, info):
        """
        Transforms requests into strings if any present.
        Default behavior also adds results to item.
        """
        requests = ItemAdapter(item).get(self.files_requests_field, [])
        if requests:
            ItemAdapter(item)[self.files_requests_field] = [
                f"{r.method} {r.url}" for r in requests
            ]

        return super().item_completed(results, item, info)

    def file_path(self, request, response=None, info=None, item=None):
        """
        Path to save the files, modified to organize the gazettes in directories
        and with the right file extension added.
        The files will be under <territory_id>/<gazette date>/<filename>.
        """
        filepath = Path(
            super().file_path(request, response=response, info=info, item=item)
        )
        # The default path from the scrapy class begins with "full/". In this
        # class we replace that with the territory_id and gazette date.
        filename = filepath.name

        if response is not None and not filepath.suffix:
            filename = self._get_filename_with_extension(filename, response)

        return str(Path("pdfs", filename))

    def _get_filename_with_extension(self, filename, response):
        # The majority of the Gazettes are PDF files, so we can check it
        # faster validating document Content-Type before using a more costly
        # check with filetype library
        file_extension = (
            ".pdf" if response.headers.get("Content-Type") == b"application/pdf" else ""
        )

        if not file_extension:
            # Checks file extension from file header if possible
            max_file_header_size = 261
            file_kind = filetype.guess(response.body[:max_file_header_size])
            file_extension = f".{file_kind.extension}" if file_kind is not None else ""

        return f"{filename}{file_extension}"