from datetime import datetime as dt, UTC
from pathlib import Path
from itemadapter import ItemAdapter
from scrapy.http import Request
from scrapy.http.request import NO_CALLBACK
from scrapy.pipelines.files import FilesPipeline
from scrapy.settings import Settings
from scrapy.utils.misc import md5sum
import filetype
import base64
import io


class DiarioOficialBotPipeline:
    def process_item(self, item, spider):
        item["territory_id"] = getattr(spider, "TERRITORY_ID")
        item["name"] = getattr(spider, "name")

        # Date manipulation to allow jsonschema to validate correctly
        item["date"] = str(item["date"])
        item["scraped_at"] = dt.now(UTC).isoformat("T") + "Z"

        return item


class DiarioOficialFilesPipeline(FilesPipeline):
    """Pipeline para baixar arquivos descritos em file_urls,
    file_requests ou _file_content (base64).

    Diferenças para o FilesPipeline padrão:
        - organiza arquivos em pasta pdfs/
        - suporta requests em file_requests
        - permite salvar arquivos em base64 via campo _file_content
        - mantém compatibilidade: 'files' no item terá path e checksum
    """

    DEFAULT_FILES_REQUESTS_FIELD = "file_requests"

    def __init__(self, store_uri, crawler, *args, **kwargs):
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
        """Gera requests apenas para file_urls e file_requests.
        O conteúdo em base64 será tratado em item_completed.
        """
        adapter = ItemAdapter(item)

        # URLs tradicionais
        urls = adapter.get(self.files_urls_field, [])
        download_file_headers = getattr(info.spider, "download_file_headers", {})
        for u in urls:
            yield Request(u, callback=NO_CALLBACK, headers=download_file_headers)

        # Requests customizados
        for r in adapter.get(self.files_requests_field, []):
            yield r

        # Não gera request para _file_content
        return []

    def item_completed(self, results, item, info):
        """Processa resultados normais e também salva arquivos em base64."""
        adapter = ItemAdapter(item)

        # Primeiro, processa o fluxo padrão
        item = super().item_completed(results, item, info)

        # Depois, lida com _file_content (base64)
        if adapter.get("_file_content"):
            data = base64.b64decode(adapter["_file_content"])
            checksum = md5sum(io.BytesIO(data))  # gera checksum

            # cria nome do arquivo baseado no checksum
            filename = f"{checksum}.pdf"
            path = str(Path("pdfs", filename))

            abs_path = Path(self.store.basedir) / path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(data)

            # adiciona no campo files
            files = adapter.get("files", [])
            url = adapter.get("_file_content_url", "")
            files.append({"url": url, "path": path, "checksum": checksum})
            adapter["files"] = files

            # remove campo auxiliar para não exportar
            del adapter["_file_content"]

        return item

    def file_path(self, request, response=None, info=None, item=None):
        """Define o path final do arquivo salvo."""
        if request is None:
            # Caso base64 → já tratado em item_completed (usa checksum no nome)
            return "pdfs/dummy.pdf"

        filepath = Path(
            super().file_path(request, response=response, info=info, item=item)
        )
        filename = filepath.name

        if response is not None and not filepath.suffix:
            filename = self._get_filename_with_extension(filename, response)

        return str(Path("pdfs", filename))

    def _get_filename_with_extension(self, filename, response):
        # A maioria é PDF, então tentamos direto
        file_extension = (
            ".pdf" if response.headers.get("Content-Type") == b"application/pdf" else ""
        )

        if not file_extension:
            # Detecta tipo pelo header do arquivo
            max_file_header_size = 261
            file_kind = filetype.guess(response.body[:max_file_header_size])
            file_extension = f".{file_kind.extension}" if file_kind is not None else ""

        return f"{filename}{file_extension}"
