from django.urls import path

from api.views import recipe_shortlink_redirect

urlpatterns = [
    path('r/<int:pk>/', recipe_shortlink_redirect, name='recipe-shortlink'),
]
