from django.views import View
from django.http import JsonResponse
from .services import get_2gis_reviews_data
from .exceptions import FetchReviewError


class Fetch2GISReviews(View): 
    def get(
        self, 
        request, 
        organization_id: str, 
    ): 
        reviews_limit = int(request.GET.get('limit', 10) )
        min_rating = int(request.GET.get('min_rating', 4))

        try:
            reviews_data, average_rating, total_reviews_count = get_2gis_reviews_data(
                organization_id=organization_id, 
                reviews_limit=reviews_limit, 
                min_rating=min_rating,
            )
        except FetchReviewError as e: 
            response = {
                'error': str(e), 
            }
            return JsonResponse(response, status=500)

        response = {
            'average_rating': average_rating, 
            'total_reviews_count': total_reviews_count, 
            'reviews': reviews_data,
        }

        return JsonResponse(response)
