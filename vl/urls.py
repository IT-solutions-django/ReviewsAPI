from django.urls import path
from .views import *


app_name = 'vl' 


urlpatterns = [
    path('reviews/<str:organization_slug>/<str:organization_id>/', FetchVLReviews.as_view(), name='fetch_vl_reviews'),
]