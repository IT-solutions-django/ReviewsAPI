from django.urls import path
from .views import *


app_name = 'two_gis' 


urlpatterns = [
    path('reviews/<str:organization_id>', Fetch2GISReviews.as_view(), name='fetch_two_gis_reviews'),
]