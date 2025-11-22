# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# *************************** api_views.py *****************************

# This file contains the api designated views for the DailyNews Application

from rest_framework import generics, permissions
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from django.db.models import Q
from .models import Article
from .serializers import ArticleSerializer


class ArticleSubscriptionAPIView(generics.ListAPIView):
    """
    API endpoint to list published articles specific to the authenticated
    client's subscriptions (Journalists and Publishers).
    """
    serializer_class = ArticleSerializer

    # Use Token Authentication (requires implementing token generation
    # in auth views)
    authentication_classes = [TokenAuthentication, BasicAuthentication]

    # Only allow access to authenticated API clients
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves articles that match the authenticated user's subscriptions.
        The authenticated user (request.user) acts as the third-party client
        account.
        """
        client_user = self.request.user

        # 1. Get lists of IDs from the client's subscription models
        subscribed_journalists = client_user.reader_journalist_subs. \
            values_list('journalist__pk', flat=True)
        subscribed_publishers = client_user.reader_publisher_subs. \
            values_list('publisher__pk', flat=True)

        # 2. Filter articles: Must be PUBLISHED AND match EITHER a journalist
        # OR a publisher subscription
        queryset = Article.objects.filter(status='PUBLISHED').filter(
            Q(author__pk__in=subscribed_journalists) |
            Q(publisher__pk__in=subscribed_publishers)
        ).order_by('-publication_date')

        return queryset

    # Override get_serializer_context to pass the request object to the
    # serializer this is necessary for constructing absolute URLs in
    # ArticleSerializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
