# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# *************************** api_urls.py ******************************

# This file contains the url paths for the app API functionality.

from django.urls import path
from . import api_views

urlpatterns = [
    # Endpoint for retrieving articles based on the authenticated user's
    # subscriptions
    path('articles/', api_views.ArticleSubscriptionAPIView.as_view(),
         name='api_subscribed_articles'),
]
