# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# ************************** serializers.py ****************************

# This file contains the serializers framework to ensure API capabilities.

from rest_framework import serializers
from .models import Article, CustomUser, Publisher


# Serializers for Nested Data
class PublisherSerializer(serializers.ModelSerializer):
    """Serializes the basic Publisher model fields."""
    class Meta:
        model = Publisher
        fields = ('id', 'name')


class JournalistSerializer(serializers.ModelSerializer):
    """Serializes the Author (CustomUser) model, including their Publisher."""
    publishers = PublisherSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        # Only expose necessary public fields for an author
        fields = ('id', 'username', 'first_name', 'last_name', 'publishers',
                  'profile_photo')


# Main Article Serializer
class ArticleSerializer(serializers.ModelSerializer):
    """Serializes the core Article model, using nested serializers for
    relationships."""

    # Use nested serializers to embed author and publisher details
    author = JournalistSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)

    # A method field to construct the full, absolute URL to the article
    article_url = serializers.SerializerMethodField()

    def get_article_url(self, obj):
        """Constructs the absolute URL for the reader to access the article."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(reverse('article_reader',
                                                      args=[obj.pk]))

        return f"/article/{obj.pk}/"

    class Meta:
        model = Article
        fields = (
            'id',
            'title',
            'body',
            'publication_date',
            'author',
            'publisher',
            'article_url',
            'featured_image'
        )
        read_only_fields = fields

# Import reverse at the end to prevent potential circular dependency issues
from django.urls import reverse
