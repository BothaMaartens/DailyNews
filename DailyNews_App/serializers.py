# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# ************************** serializers.py ****************************

"""
serializers.py
==============

This module defines the Django REST Framework serializers for the
DailyNews API.

It is responsible for transforming complex database models (Article,
CustomUser, Publisher)
into native Python datatypes (and eventually JSON) for API consumption.

Key Features:
    * **Nested Serialization:** Embedding Publisher and Author details
        directly within Article responses.
    * **Dynamic Fields:** Generating absolute URLs for articles based on the
        current request context.
    * **Field Filtering:** exposing only public-safe fields for
    Users (Journalists).
"""

from rest_framework import serializers
from .models import Article, CustomUser, Publisher


# Serializers for Nested Data
class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializes the ``Publisher`` model for API responses.

    Typically used as a nested representation within `ArticleSerializer`.

    :ivar id: The database primary key.
    :ivar name: The name of the publisher.
    """
    class Meta:
        model = Publisher
        fields = ('id', 'name')


class JournalistSerializer(serializers.ModelSerializer):
    """
    Serializes the ``CustomUser`` model specifically for displaying
    Author details.

    It filters out sensitive user information (like password, email, etc.) and
    includes the associated publishers.

    :ivar publishers: A list of nested ``PublisherSerializer`` objects.
    :ivar profile_photo: URL to the user's profile image.
    """
    publishers = PublisherSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        # Only expose necessary public fields for an author
        fields = ('id', 'username', 'first_name', 'last_name', 'publishers',
                  'profile_photo')


# Main Article Serializer
class ArticleSerializer(serializers.ModelSerializer):
    """
    The primary serializer for the ``Article`` model.

    It provides a complete representation of a news article, including full
    details of the Author and Publisher using nested serializers.

    :ivar author: Nested ``JournalistSerializer`` representation.
    :ivar publisher: Nested ``PublisherSerializer`` representation.
    :ivar article_url: Calculated field containing the full absolute URL to
        the article.
    """

    # Use nested serializers to embed author and publisher details
    author = JournalistSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)

    # A method field to construct the full, absolute URL to the article
    article_url = serializers.SerializerMethodField()

    def get_article_url(self, obj):
        """
        Generates the absolute URL for the article reader view.

        Uses the request context (if available) to build a full URI
        (including domain), otherwise falls back to a relative path.

        :param obj: The Article instance being serialized.
        :return: String URL
        """
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
