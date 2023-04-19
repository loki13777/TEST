# основная логика паука
import time
from bs4 import BeautifulSoup
import scrapy
from project1.spiders.url_categories import get_urls
import json
from project1.spiders.constants import *


class AptekaSpider(scrapy.Spider):
    name = "test"
    start_urls = ['https://apteka-ot-sklada.ru']

    def parse(self, response: scrapy.http.Response) -> scrapy.http.Response:
        # отправляем post запрос с id нужного нам города
        request = scrapy.Request(POST_CITY_URL, method='POST',
                                 body=json.dumps(ID_CITY),
                                 headers=HEADERS,
                                 callback=self.parse_results)

        yield request

    def parse_results(self, response: scrapy.http.Response) -> scrapy.http.Response:
        # шлём запрос по каждому URL категории
        for el in get_urls():
            yield scrapy.Request(el, callback=self.parse_items)

    def parse_items(self, response: scrapy.http.Response) -> scrapy.http.Response:
        # получаем URL каждой крточки товара на странице категории и отправляем запрос
        list_end_card_url = response.css(CSS_CARD_URL).getall()
        for end_card_url in list_end_card_url:
            yield scrapy.Request(START_URL + end_card_url, callback=self.parse_data)
        # получаем ссылку на следующую страницу и рекурсивно передаём ответ в текущую функцию
        next_page_raw_url = response.css(CSS_NEXT_PAGE).get()
        if next_page_raw_url is not None:
            yield scrapy.Request(START_URL + next_page_raw_url, callback=self.parse_items)
    # в следующих методах получаем нужную нам информацию из карточек через css селекторы

    @staticmethod
    def get_product_code(response: scrapy.http.Response) -> str:
        return response.url.split('_')[-1]

    @staticmethod
    def get_title(response: scrapy.http.Response) -> str:
        return response.css(CSS_TITLE).get()

    @staticmethod
    def get_marketing_tags(response: scrapy.http.Response) -> list[str]:
        marketing_tags = response.css(CSS_MARKETING_TAGS).getall()
        return [tag.strip() for tag in marketing_tags]

    @staticmethod
    def get_brand(response: scrapy.http.Response) -> str:
        return response.css(CSS_BRAND).get()

    @staticmethod
    def get_section(response: scrapy.http.Response) -> list:
        return response.css(CSS_SECTION).getall()

    @staticmethod
    def get_original_price(response: scrapy.http.Response) -> float | None:
        original_price = response.css(CSS_ORIGINAL_PRICE).get()
        return float(original_price) if original_price else None

    @staticmethod
    def get_in_stock(response: scrapy.http.Response) -> bool:
        return not bool(response.css(CSS_IN_STOCK).get())

    @staticmethod
    def get_list_images(response: scrapy.http.Response) -> list[str]:
        list_images = response.css(CSS_LIST_IMAGES).getall()
        return [START_URL + image for image in list_images]

    @staticmethod
    def get_main_image(list_images: list[str]) -> str:
        return list_images[0] if list_images else ''

    @staticmethod
    def get_metadata(response: scrapy.http.Response) -> str | None:
        metadata = response.css(CSS_METADATA).get()
        if metadata:
            soup = BeautifulSoup(metadata, 'html.parser')
            return soup.get_text()

    @staticmethod
    def get_country(response: scrapy.http.Response) -> str:
        return response.css(CSS_COUNTRY).get()

    def parse_data(self, response: scrapy.http.Response) -> dict:
        # собираем полученные данные из каждой карточки в словарь
        timestamp = time.time()
        rpc = self.get_product_code(response)
        url = response.url
        title = self.get_title(response)
        marketing_tags = self.get_marketing_tags(response)
        brand = self.get_brand(response)
        section = self.get_section(response)
        original_price = self.get_original_price(response)
        in_stock = self.get_in_stock(response)
        list_images = self.get_list_images(response)
        main_image = self.get_main_image(list_images)
        list_images = list_images[1:]
        description = self.get_metadata(response)
        country = self.get_country(response)

        result_dict = {
            "timestamp": timestamp,
            "RPC": rpc,
            "url": url,
            "title": title,
            "marketing_tags": marketing_tags,
            "brand": brand,
            "section": section,
            "price_data": {
                "current": original_price,
                "original_price": original_price,
                "sale_tag": "",
            },
            "stock": {
                "in_stock": in_stock,
                "count": 0,
            },
            "assets": {
                "main_image": main_image,
                "set_images": list_images,
                "view360": [],
                "video": [],
            },
            "metadata": {
                "__description": description,
                "СТРАНА ПРОИЗВОДИТЕЛЬ": country,
            },
            "variants": 1,
        }

        yield result_dict
