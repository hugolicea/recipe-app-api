"""
Url mappings for recipe app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from recipe import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)
router.register('tags', views.TagViewSet)

# The app name for namespacing the URLs
app_name = 'recipe'

# The URL patterns for the recipe app
urlpatterns = [
    path('', include(router.urls)),
]
