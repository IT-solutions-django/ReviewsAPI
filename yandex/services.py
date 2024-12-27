from vl.services import convert_to_datetime
import requests 
from bs4 import BeautifulSoup
from typing import Any


def get_yandex_reviews_data(
    organization_slug: str, 
    organization_id: int,
    reviews_limit: int, 
    min_rating: int
) -> tuple[dict[str, Any], float, int]:
    """
    Параметры:
    organization_slug (str): Слаг компании на Яндекс Картах. Пример: "naparili_dv"
    organization_id (str): ID компании на Яндекс Картах. Пример: 68956168702
    limit (int): Максимальное количество отзывов
    min_rating (int): Минимальная оценка отзыва

    Возвращает:
    list[dict], float, int: Возвращает список отзывов, средний рейтинг компании и общее количество отзывов
    """
    url = f'https://yandex.ru/maps/org/{organization_slug}/{organization_id}/reviews/'
    
    headers = {
        'Host': 'yandex.ru',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Cookie': 'maps_los=0; spravka=dD0xNzI2ODEwMTY3O2k9ODYuMTAyLjEzLjc0O0Q9RUY3MDRCMEVFNzU0MTg1N0YzNTZENDg2RjlGMjNFNDMzNTY2NDdDRUQxQzlFQzE3NTFEQThDREFGMjA4MTNFNENFMUFFNkQyRTNCOTBGRTc3NENEOEJFQTExNUVFNjQwRUQwOEIwNDQ2QjI0NUYyRkVBQkEwMzNEMzQxM0JFNzA1MEQ0MzMyOTlGRkY1M0I4MUJERDt1PTE3MjY4MTAxNjc2NTgyNzE1ODA7aD01YmYzMGNlNTBmYTY4ODljZWI0ZmM5NjcyOTI4MGJmOQ==; _yasc=r3AyN1rNx3P7SuIwvwYQHGPC7jhpypevF0XoRv0aqOsiu8Q5dsPbKyhN0qIj9ZEhnAHqypxgYP8=; i=USTWwFikzzttv4Ewt+JjX6guEjI7ryOi3U8d1d0obMvWdQLf6l3nC4o08OxIR2X5+xwqxB4bIfVflox4XzmFHzUvDKI=; yandexuid=1948173161726810137; yashr=8704804031726810137; receive-cookie-deprecation=1; yuidss=1948173161726810137; ymex=2042170139.yrts.1726810139; _ym_uid=1726810140413132111; _ym_d=1726810140; is_gdpr=0; is_gdpr_b=CLmcHRCIlAIoAg==; yp=2042170169.pcs.1#1729488569.hdrc.0#1727414969.szm.0_8:2400x1350:2400x1194; bh=YNvqsLgGahfcyuH/CJLYobEDn8/14QyChPKOA4vBAg==; yabs-vdrf=A0; gdpr=0',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i',
    }

    response = requests.get(url, headers=headers).text
    soup = BeautifulSoup(response, "html.parser")
    meta_block = soup.find('div', class_='business-summary-rating-badge-view')

    rating_raw = meta_block.find('div', class_='business-summary-rating-badge-view__rating').text
    average_rating = float(rating_raw.split('\xa0')[1].replace(',', '.'))

    reviews_count_raw = meta_block.find('span', class_='business-rating-amount-view').text 
    reviews_count = int(reviews_count_raw.split()[0])

    review_blocks = soup.findAll('div', class_='business-reviews-card-view__review')
    reviews = []
    for review_block in review_blocks: 
        author = review_block.find('div', class_='business-review-view__author-name').find('span').text 
        text = review_block.find('span', class_='business-review-view__body-text').text
        stars = len(review_block.find('div', class_='business-rating-badge-view__stars').findAll('span'))

        created_at_str = review_block.find('span', class_='business-review-view__date').find('span').text 
        created_at = convert_to_datetime(created_at_str)

        author_avatar = review_block.find('div', class_='user-icon-view__icon').get('style')
        if author_avatar: 
            author_avatar = author_avatar.split('url(')[1][:-1]

        photos_blocks = review_block.findAll('img', class_='business-review-media__item-img')
        photos = [photo_block.get('src') for photo_block in photos_blocks]

        if stars >= min_rating:
            reviews.append({
                'rating': stars, 
                'created_at': created_at,
                'review_text': text,
                'author_name': author,
                'author_avatar_url': author_avatar,
                'review_photos': photos,
            })

    return reviews[:reviews_limit], average_rating, reviews_count