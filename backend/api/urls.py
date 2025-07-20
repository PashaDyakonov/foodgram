from drf_spectacular.views import SpectacularSwaggerView
from django.urls import include, path
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
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),
]
