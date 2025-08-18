
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers

from api.views import (
    IngredientsViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet,
)


router = routers.DefaultRouter()

router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientsViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'),
         ),
]
