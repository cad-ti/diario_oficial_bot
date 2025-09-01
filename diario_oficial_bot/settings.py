BOT_NAME = "diario_oficial_bot"
SPIDER_MODULES = ["diario_oficial_bot.spiders"]
NEWSPIDER_MODULE = "diario_oficial_bot.spiders"
USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0"
ROBOTSTXT_OBEY = False

ITEM_PIPELINES = {
    "diario_oficial_bot.pipelines.DiarioOficialBotPipeline": 300,
    "diario_oficial_bot.pipelines.DiarioOficialFilesPipeline": 300,
}

FEED_EXPORTERS = {
    'csv': 'diario_oficial_bot.feed_exporters.CsvNoHeaderExporter',
}



REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

DOWNLOAD_TIMEOUT = 360

FILES_STORE = "data"
MEDIA_ALLOW_REDIRECTS = True

