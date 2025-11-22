# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# ***************************** tests.py *******************************

# This file will contain the unit tests to validate the
# ArticleSubscriptionAPIView.

# DailyNews_App/tests.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Article, Publisher, JournalistSubscription
from .models import PublisherSubscription

# Import the necessary model for token generation
from rest_framework.authtoken.models import Token
from datetime import datetime

User = get_user_model()


class ArticleSubscriptionAPITest(APITestCase):
    """
    Tests the ArticleSubscriptionAPIView endpoint to ensure correct
    subscription-based filtering and authentication.
    """

    def setUp(self):
        # 1. Create Publishers
        self.publisher1 = Publisher.objects.create(name="Daily Globe")
        self.publisher2 = Publisher.objects.create(name="Tech Weekly")

        # 2. Create Users (Journalists and Readers)
        self.journalist1 = User.objects.create_user(
            username='j1',
            email='j1@news.com',
            password='password',
            role='JOURNALIST'
        )
        self.journalist1.publishers.add(self.publisher1)  # Affiliated with P1

        self.journalist2 = User.objects.create_user(
            username='j2',
            email='j2@news.com',
            password='password',
            role='JOURNALIST'
        )
        self.journalist2.publishers.add(self.publisher2)  # Affiliated with P2

        # The API Client/Reader (the user making the API calls)
        self.api_client_user = User.objects.create_user(
            username='api_client',
            email='client@api.com',
            password='password',
            role='READER'
        )
        # Manually create the token for the API client
        self.token, created = Token.objects.get_or_create(
            user=self.api_client_user)
        self.api_url = reverse('api_subscribed_articles')

        # 3. Create Articles (ensure they are PUBLISHED for the view)
        # Article 1: By J1, Published by P1
        self.article1 = Article.objects.create(
            title="P1 J1 Article",
            author=self.journalist1,
            publisher=self.publisher1,
            status='PUBLISHED',
            publication_date=datetime(2025, 11, 15)
        )
        # Article 2: By J2, Published by P2
        self.article2 = Article.objects.create(
            title="P2 J2 Article",
            author=self.journalist2,
            publisher=self.publisher2,
            status='PUBLISHED',
            publication_date=datetime(2025, 11, 14)
        )
        # Article 3: By J1, but status is DRAFT (Should NEVER be visible)
        self.article3_draft = Article.objects.create(
            title="Draft Article",
            author=self.journalist1,
            publisher=self.publisher1,
            status='DRAFT',
            publication_date=datetime(2025, 11, 13)
        )
        # Article 4: By J2, Published by P1 (Cross-publisher article)
        self.article4_cross = Article.objects.create(
            title="Cross Article",
            author=self.journalist2,
            publisher=self.publisher1,
            status='PUBLISHED',
            publication_date=datetime(2025, 11, 16)
        )

    def test_unauthenticated_access_is_denied(self):
        """Ensure requests without a token are rejected."""
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_subscribes_to_journalist_only(self):
        """Client subscribes to J1 and should see J1's articles."""
        # Subscribe client to Journalist 1
        JournalistSubscription.objects.create(
            reader=self.api_client_user, journalist=self.journalist1
        )

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only A1 matches J1 subscription (Author J1). Expected 1.
        self.assertEqual(len(response.data), 1)

        titles = [item['title'] for item in response.data]
        self.assertIn(self.article1.title, titles)
        self.assertNotIn(self.article2.title, titles)

    def test_client_subscribes_to_publisher_only(self):
        """Client subscribes to P2 and should see all P2 articles."""
        # Subscribe client to Publisher 2
        PublisherSubscription.objects.create(
            reader=self.api_client_user, publisher=self.publisher2
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only A2 (J2, P2)

        titles = [item['title'] for item in response.data]
        self.assertIn(self.article2.title, titles)
        self.assertNotIn(self.article1.title, titles)

    def test_client_subscribes_to_both(self):
        """Client subscribes to J1 and P2 and should see articles from both."""
        # Subscribe to J1 and P2
        JournalistSubscription.objects.create(
            reader=self.api_client_user, journalist=self.journalist1
        )
        PublisherSubscription.objects.create(
            reader=self.api_client_user, publisher=self.publisher2
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # FIX: A1 matches J1. A2 matches P2. A4_cross matches neither.
        self.assertEqual(len(response.data), 2)

        titles = [item['title'] for item in response.data]
        self.assertIn(self.article1.title, titles)
        self.assertIn(self.article2.title, titles)
        self.assertNotIn(self.article4_cross.title, titles)

    def test_only_published_articles_are_returned(self):
        """Ensure DRAFT articles are always excluded, regardless of
        subscription."""
        # Subscribe client to Journalist 1
        JournalistSubscription.objects.create(
            reader=self.api_client_user, journalist=self.journalist1
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(self.api_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item['title'] for item in response.data]
        self.assertNotIn(self.article3_draft.title, titles)
