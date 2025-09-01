import scrapy


class Gazette(scrapy.Item):
    name = scrapy.Field()
    territory_id = scrapy.Field()
    date = scrapy.Field()
    edition_number = scrapy.Field()
    is_extra_edition = scrapy.Field()
    power = scrapy.Field()
    file_urls = scrapy.Field()
    files = scrapy.Field()
    scraped_at = scrapy.Field()