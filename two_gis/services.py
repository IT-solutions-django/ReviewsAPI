from django.shortcuts import render
import requests
from .exceptions import FetchReviewError, EmptyReviewList
from requests.adapters import Retry, HTTPAdapter
from typing import Any
import os 
from dotenv import load_dotenv
import time
import random


load_dotenv()


def get_2gis_reviews_data(
        organization_id: str, 
        reviews_limit: int = 10, 
        min_rating: int = 4
    ):
    """
    Получаем информацию об отзывах определенной организации с поддержкой повторных попыток
    при возникновении ошибки EmptyReviewList.
    """
    api_key_2gis = os.getenv('2GIS_API_KEY')

    MAX_RETRIES = 3

    for attempt in range(MAX_RETRIES):
        try:
            fetched_reviews = _fetch_reviews(
                organization_id=organization_id,
                api_key_2gis=api_key_2gis
            )
            result = _get_needed_data_format(
                fetched_data=fetched_reviews, 
                reviews_limit=reviews_limit, 
                min_rating=min_rating
            )
            average_rating = fetched_reviews['meta']['branch_rating']
            count_review = fetched_reviews['meta']['branch_reviews_count']
            return result, average_rating, count_review
        
        except EmptyReviewList as e:
            print(f"Попытка {attempt + 1}/{MAX_RETRIES} - Ошибка: {e}")
            if attempt < MAX_RETRIES - 1:  
                time.sleep(random.randint(2, 6))
            else:
                raise FetchReviewError(f"Не удалось получить данные: {e}")

        # except Exception as e:
        #     raise FetchReviewError(f"Не удалось получить данные: {e}")


def _fetch_reviews(
        organization_id: str, 
        api_key_2gis: str, 
    ) -> dict[str, dict]:
    """
    Использую публичное API 2gis, получаем полную информацию об отзывах организации.
    :param api_key_2gis: 2GIS API KEY
    :param organization_id: ID организации 2gis
    :return: Словарь ответа 2gis API
    """

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        return session.get(
            f"https://public-api.reviews.2gis.com/2.0/branches/{organization_id}/reviews?"
            f"limit=50&is_advertiser=false&fields=meta.branch_rating,meta.branch_reviews_count&sort_by=date_edited&"
            f"key={api_key_2gis}&locale=ru_RU"
        ).json()
    except Exception:
        raise FetchReviewError("Ошибка при запросе к 2gis API")


def _get_needed_data_format(
        fetched_data: dict[str, dict], 
        reviews_limit: int = 10, 
        min_rating = 4
    ) -> dict[str, Any]:
    """
    Фильтрация ненужных данных ответа и преобразование нужных в необходимый формат.
    :param fetched_data: Данные ответа от API 2gis;
    :param reviews_limit: Количество отзывов в ответе (default: 10);
    :return: Словарь с данными об отзывах организации
    """

    if len(fetched_data["reviews"]) == 0:
        raise EmptyReviewList("Список отзывов пуст")
    
    return {
        "reviews": [
            {
                "rating": review["rating"],
                "created_at": review["date_edited"] or review["date_created"],
                "review_text": review["text"],
                "author_name": review["user"]["name"],
                "author_avatar_url": review["user"]["photo_preview_urls"]["640x"],
                "review_photos": [
                    photo["preview_urls"]["640x"]
                    for photo in review["photos"]
                    if photo.get("preview_urls")
                ],
            }
            for review in fetched_data["reviews"]
            if review["rating"] >= min_rating
        ][:reviews_limit],
    }