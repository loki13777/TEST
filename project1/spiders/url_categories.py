# читаем json и возвращаем список URL категорий сайта
import json


def get_urls(name_file: str = 'urls_test_spider.json') -> list[str]:
    with open(name_file, 'r') as file:
        list_urls = json.load(file)
        return list_urls
