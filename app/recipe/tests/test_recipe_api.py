"""
Tests for recipe APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'link': 'http://example.com/recipe.pdf',
        'description': 'Sample description',
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        """Set up the test client."""
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        """Set up the test client and authenticate the user."""
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = create_user(email='other@example.com', password='test123')
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test viewing a recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.25'),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test partial update of a recipe."""
        original_link = 'http://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Original title',
            link=original_link
        )

        payload = {'title': 'New title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test full update of a recipe."""
        recipe = create_recipe(
            user=self.user,
            title='Original title',
            link='http://example.com/recipe.pdf',
            description='Original description',
        )

        payload = {
            'title': 'New title',
            'time_minutes': 25,
            'price': Decimal('5.00'),
            'link': 'http://example.com/new-recipe2.pdf',
            'description': 'New description',
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_user_recipe_error(self):
        """Test deleting other user's recipe returns error."""
        other_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_update_user_returns_error(self):
        """Test updating user returns error."""
        new_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=self.user)
        payload = {'user': new_user}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_create_recipe_with_new_tag(self):
        """Test creating a recipe with new tag."""
        tag_name = 'Test tag'
        tag_name1 = 'Test tag1'
        payload = {
            'title': 'Test recipe',
            'time_minutes': 10,
            'price': Decimal('5.99'),
            'tags': [{'name': tag_name}, {'name': tag_name1}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        for tag in tags:
            self.assertTrue(
                recipe.tags.filter(
                    name=tag.name,
                    user=self.user,
                ).exists()
            )

    def test_create_recipe_with_existing_tag(self):
        """Test creating a recipe with existing tag."""
        tag = Tag.objects.create(user=self.user, name='Test tag')
        tag1 = Tag.objects.create(user=self.user, name='Test tag1')
        payload = {
            'title': 'Test recipe',
            'time_minutes': 10,
            'price': Decimal('5.99'),
            'tags': [
                {'name': tag.name},
                {'name': tag1.name},
                {"name": "Test tag2"}
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 3)
        self.assertTrue(
            recipe.tags.filter(
                name=tag.name,
                user=self.user,
            ).exists()
        )

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe."""
        tag = Tag.objects.create(user=self.user, name='Test Lunch')
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': tag.name}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(name=tag.name)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag = Tag.objects.create(user=self.user, name='Test Lunch')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        new_tag = Tag.objects.create(user=self.user, name='Test Dinner')
        payload = {
            'tags': [{'name': new_tag.name}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(new_tag, recipe.tags.all())
        self.assertNotIn(tag, recipe.tags.all())

    def test_clear_recipe_taf(self):
        """Test clearing tags when updating a recipe."""
        tag = Tag.objects.create(user=self.user, name='Test Lunch')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {
            'tags': [],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
