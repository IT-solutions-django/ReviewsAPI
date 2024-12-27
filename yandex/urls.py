from django.urls import path
from .views import *


app_name = 'vl' 


urlpatterns = [
    path('reviews/<str:organization_slug>/<str:organization_id>', FetchYandexReviews.as_view(), name='fetch_yandex_reviews'),
]