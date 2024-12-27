import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Any


def get_vl_reviews_data(
        organization_slug: str, 
        organization_id: int, 
        limit: int, 
        min_rating: int
) -> tuple[dict[str, Any], float, int]:
    """
    Параметры:
    organization_slug (str): Слаг компании на vl.ru. Пример: "naparili-dv"
    organization_id (int): ID компании на vl.ru. Пример: 444287
    limit (int): Максимальное количество отзывов
    min_rating (int): Минимальная оценка отзыва

    Возвращает:
    list[dict], float, int: Возвращает список отзывов, средний рейтинг компании и общее количество отзывов

    """
    url = f"https://www.vl.ru/commentsgate/ajax/thread/company/{organization_slug}/embedded"

    params = {
        "theme": "company",
        "appVersion": "2024101514104",
        "_dc": "0.32945840348689304",
        "pastafarian": "0fb682602c07c4ae9bdb8969e7c43add3b898f4e7b14548c8c2287a29032d6b1",
        "location": f"https://www.vl.ru/{organization_slug}#comments",
        "moderatorMode": "1"
    }

    headers = {
        "Host": "www.vl.ru",
        "Sec-Ch-Ua-Platform": "\"macOS\"",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Language": "ru-RU,ru;q=0.9",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Sec-Ch-Ua": "\"Chromium\";v=\"129\", \"Not=A?Brand\";v=\"8\"",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.71 Safari/537.36",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.vl.ru/autocenter",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i"
    }

    cookies = {
        "PHPSESSID": "rhjcp9pkfg82bvcda7tve2a9m0",
        "city": "4",
        "region": "103",
        "visitor": "ad5f2acbb35cd457a9dc57c692437d9261e1d5606ea33280caabd64f0fa3d0d6",
        "ring": "980791ab6a297547f26234387e1a5012",
        "analytics_user": "980791ab6a297547f26234387e1a5012",
        "spravochnik_windowSessionID": "ad061bf1730033306880",
        "_ym_uid": "1730033307709177970",
        "_ym_d": "1730033307",
        "sprRecentlyWatchedCompanyIds": "460034",
        "_ym_isad": "2",
        "_gid": "GA1.2.1877505797.1730033311",
        "_ga": "GA1.3.1517315620.1730033307",
        "_ga_3XHX5WMXEB": "GS1.2.1730033312.1.0.1730033312.60.0.0",
        "_ga_D3RZ9TRN3Y": "GS1.3.1730033312.1.0.1730033312.60.0.0",
        "_ga_1XW1PCV9KF": "GS1.2.1730033312.1.1.1730034975.8.0.0",
        "_ym_visorc": "w",
        "spravochnik_windowSessionTS": "1730035316115",
        "_ga_3X07YH0D78": "GS1.1.1730035314.2.1.1730035316.0.0.0",
        "_gat": "1",
        "_gat_allProjects": "1",
        "_gat_glCommonTracker": "1",
        "_gat_commentsvlru": "1",
    }

    response = requests.get(url, headers=headers, params=params, cookies=cookies)

    if response.status_code == 200:
        res = response.json()['data']['content']
        soup = BeautifulSoup(res, 'html.parser')

        best_comments_block = soup.find('div', class_='best-comments')

        review_elements = soup.find_all('li', {'data-type': 'review'})

        if best_comments_block: 
            review_elements += best_comments_block.find_all('li')

        reviews = []

        for review in review_elements:
            star_rating = review.find('div', class_='star-rating')
            if star_rating:
                star_rating = int(float(star_rating.find('div', class_='active')['data-value']) * 5)
            else:
                continue

            user_avatar = review.find('div', class_='user-avatar').find('img')
            if user_avatar:
                user_avatar = user_avatar['src']

            user_name_tag = review.find('span', class_='user-name')
            user_name = user_name_tag.text.strip() if user_name_tag else 'N/A'

            review_text_tag = review.find('div', class_='cmt-content').find('p', class_='comment-text')
            if review_text_tag and "Комментарий:" in review_text_tag.text:
                review_text = review_text_tag.text.strip().split("Комментарий:", 1)[1].strip()
            else:
                continue

            time_tag = review.find('span', class_='time')
            time_text = time_tag.text 
            created_at = convert_to_datetime(time_text)

            photos = []
            photos_block = review.find('div', class_='comment-images')
            if photos_block: 
                photos_elements = photos_block.find_all('a')
                for photo_element in photos_elements: 
                    photos.append(photo_element.get('href'))

            if star_rating >= min_rating:
                reviews.append({
                    'rating': star_rating, 
                    'created_at': created_at,
                    'review_text': review_text,
                    'author_name': user_name,
                    'author_avatar_url': user_avatar,
                    'photos': photos,
                })

        print(soup.find('div', class_='new-favorites'))

        reviews_count_block = soup.find('div', class_='cmt-thread-subscription')
        reviews_count = reviews_count_block.find('span',class_='count').text

        api_review_avg = f'https://www.vl.ru/ajax/company-history-votes?companyId={organization_id}'
        response = requests.get(api_review_avg, headers=headers)

        data = response.json()
        average_rating_history: dict = data["history"]
        average_rating = list(average_rating_history.values())[0]

        return reviews[:limit], average_rating, reviews_count
    else:
        print(f"Ошибка: {response.status_code}")


def convert_to_datetime(datetime_str: str) -> datetime: 
    months_mapper = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12
    }

    if len(datetime_str.split()) == 2: 
        datetime_parts = datetime_str.split()
        day = datetime_parts[0] 
        year = datetime.now().year
    else: 
        datetime_parts = datetime_str.split()
        year = datetime_parts[2]
        day = datetime_parts[0]
        month_text = datetime_parts[1]

    month_text = datetime_parts[1]
    month = months_mapper.get(datetime_parts[1])

    if not month: 
        raise KeyError(f'Месяца "{month_text}" не существует')
        
    datetime_obj = datetime(
        year=int(year), 
        month=int(month), 
        day=int(day)
    ).replace(tzinfo=timezone.utc) 
    return datetime_obj