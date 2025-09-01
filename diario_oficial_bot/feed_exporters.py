import os
from scrapy.exporters import CsvItemExporter

class CsvNoHeaderExporter(CsvItemExporter):
    def __init__(self, file, **kwargs):
        # Checa se o arquivo já existe e não está vazio
        file_exists = hasattr(file, "name") and os.path.exists(file.name) and os.path.getsize(file.name) > 0

        # Se já existir, não escreve o cabeçalho
        kwargs["include_headers_line"] = not file_exists

        super().__init__(file, **kwargs)
