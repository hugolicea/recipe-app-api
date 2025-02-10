"""
Views for the recipe API.
"""
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """
    View for managing recipe APIs.

    Provides `list`, `create`, `retrieve`, `update`, and `destroy` actions.
    """
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve recipes for the authenticated user.

        Returns:
            QuerySet: A queryset of recipes filtered by the authenticated user.
        """
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """
        Return the serializer class for the request.

        Returns:
            Serializer class: The serializer class to be used for the request.
        """
        if self.action == 'list':
            return serializers.RecipeSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a new recipe.

        Args:
            serializer (Serializer): The serializer instance containing
            the validated data.
        """
        serializer.save(user=self.request.user)


class TagViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    View for managing tags API.

    Provides `list` action.
    """
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve tags for the authenticated user.

        Returns:
            QuerySet: A queryset of tags filtered by the authenticated user.
        """
        return self.queryset.filter(user=self.request.user).order_by('-name')
