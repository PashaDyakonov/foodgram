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
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
