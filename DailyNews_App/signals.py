# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# **************************** signals.py ******************************

"""
signals.py
==========

This module contains Django signal receivers that handle automated background
tasks.

Key features handled here:
    1. **System Setup:** Automatically creating User Groups and assigning
        Permissions after migration.
    2. **User Onboarding:** Assigning users to groups and generating API tokens
        upon registration.
    3. **Content Distribution:** Sending emails to subscribers and posting to
        social media (X/Twitter) when an article is published.
"""

from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.core.mail import send_mass_mail
from django.conf import settings
from django.urls import reverse
from .models import Publisher, Article, JournalistSubscription
from .models import PublisherSubscription, USER_ROLES
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import requests

User = get_user_model()


# GROUP CREATION
@receiver(post_migrate)
def create_initial_groups(sender, apps, **kwargs):
    """
    Signal receiver that initializes the database with required User Groups
    and Permissions.

    **Trigger:** Runs automatically after the ``migrate`` command is executed.

    **Actions:**
        * Ensures required 'ActualToday' and 'SportToday' publishers exist.
        * Creates 'Editor', 'Journalist', and 'Reader' groups.
        * Assigns model-level permissions (add, change, delete, view) to
            these groups.

    :param sender: The AppConfig that sent the signal.
    :param apps: A registry of the installed applications.
    :param kwargs: Additional keyword arguments.
    """
    # Ensure this runs only for the app whose config sent the signal
    if sender.name != 'DailyNews_App':
        return

    Publisher.ensure_publishers_exist()

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    # Article = apps.get_model('DailyNews_App', 'Article')

    # Define Groups and their simple permissions
    GROUPS_PERMISSIONS = {
        'Editor': {
            'article': ['change', 'delete', 'view', 'publish'],
        },
        'Journalist': {
            # Standard CRUD permissions for the Journalist's own articles
            'article': ['add', 'change', 'view', 'delete'],
        },
        'Reader': {
            # Readers can view articles.
            'article': ['view'],

            # Readers need permission to ADD/DELETE JournalistSubscription.
            'journalistsubscription': ['add', 'delete'],

            # Readers need permission to ADD/DELETE PublisherSubscription.
            'publishersubscription': ['add', 'delete'],
        }
    }

    print("--- Checking/Creating Initial User Groups ---")

    for group_name in GROUPS_PERMISSIONS:
        new_group, created = Group.objects.get_or_create(name=group_name)

        if created:
            print(f"✅ Created User Group: {group_name}")

        # Assign Permissions
        for model_name, codename_suffixes in GROUPS_PERMISSIONS[group_name]\
                .items():
            try:
                # Find the ContentType for the model
                content_type = ContentType.objects.get(
                    app_label='DailyNews_App', model=model_name)
            except ContentType.DoesNotExist:
                print(f"⚠️ ContentType for model '{model_name}' not found.\n"
                      f"Skipping permissions for {group_name}.")
                continue

            # Get and assign the actual permission objects
            for codename_suffix in codename_suffixes:
                codename = f"{codename_suffix}_{model_name}"

                try:
                    permission = Permission.objects.get(
                        content_type=content_type, codename=codename)
                    new_group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"⚠️ Permission '{codename}' not found. Skipping.")

    print("--- Initial User Group Setup Complete ---")


@receiver(post_save, sender=Article)
def handle_article_publication_and_sharing(sender, instance, created,
                                           **kwargs):
    """
    Handles notifications and social media sharing when an Article is
    published.

    **Trigger:** Runs after an ``Article`` instance is saved.

    **Logic:**
        1. Checks if the article status is 'PUBLISHED'.
        2. **Email Notification:** Aggregates emails of subscribers
            (to the Author or Publisher), removes duplicates, and sends a
            mass email.
        3. **Social Media:** Constructs a payload and sends a POST request to
            the X (Twitter) API if credentials are configured.

    :param sender: The model class (Article).
    :param instance: The actual Article instance being saved.
    :param created: Boolean indicating if this is a new record.
    """
    # Only proceed if the article is PUBLISHED
    if not created and instance.status == 'PUBLISHED':

        # --- 1. Email Subscribers ---

        # Get all readers subscribed to this article's author (Journalist)
        journalist_subscribers = JournalistSubscription.objects.filter(
            journalist=instance.author
        ).values_list('reader__email', flat=True)

        # Get all readers subscribed to this article's publisher
        publisher_subscribers = PublisherSubscription.objects.filter(
           publisher=instance.publisher
        ).values_list('reader__email', flat=True)

        # Combine and de-duplicate the email list
        recipient_list = set(list(journalist_subscribers) +
                             list(publisher_subscribers))

        if recipient_list:
            article_url = f"{settings.BASE_URL}{reverse('article_reader', args=[instance.pk])}"

            subject = (f"NEW ARTICLE: {instance.title} by "
                       f"{instance.author.get_full_name() or
                          instance.author.username}"
                        )

            message = (
                f"Dear Subscriber,\n\n"
                f"A new article, '{instance.title}', has been published by "
                f"{instance.author.get_full_name() or
                   instance.author.username} "
                f"at {instance.publisher.name}.\n\n"
                f"Read it here: {article_url}\n\n"
                f"Thank you for subscribing!"
            )

            # Django's send_mass_mail is efficient for sending many emails
            mail_tuples = []
            for recipient in recipient_list:
                mail_tuples.append((
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient]
                ))

            # Send emails
            send_mass_mail(tuple(mail_tuples), fail_silently=True)
            print(f"Sent publication email for '{instance.title}' to "
                  f"{len(recipient_list)} subscribers.")

        # 2. Post to X (Twitter) API

        api_url = "https://api.twitter.com/2/tweets"  # Placeholder endpoint

        # Check if API keys are configured (prevents errors during setup)
        if hasattr(settings, 'X_USER_ACCESS_TOKEN') and \
                settings.X_USER_ACCESS_TOKEN:
            try:
                # Construct the tweet text
                article_url = f"{settings.BASE_URL}{reverse('article_reader', args=[instance.pk])}"
                tweet_text = (
                    f"NEW: {instance.title} by {instance.author.username} for "
                    f" {instance.publisher.name}. "
                    f"Read more: {article_url} #DjangoNews"
                )

                # Placeholder for X API authorization (requires OAuth 1.0 or
                # 2.0 implementation)
                headers = {
                    "Authorization": f"Bearer {settings.X_USER_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }

                # Payload for the tweet
                payload = {"text": tweet_text}

                # Make the request using Python's 'requests' module
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload
                )

                if response.status_code == 201:
                    print(f"Successfully posted article '{instance.title}' "
                          f"to X.")
                else:
                    print(f"Failed to post to X: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"Error calling X API: {e}")


@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance, created, **kwargs):
    """
    Automatically assigns a new User to a Django Group based on their
    selected role.

    **Trigger:** Runs after a ``User`` instance is created.

    :param sender: The model class (CustomUser).
    :param instance: The user instance.
    :param created: Boolean, True if this is a new user.
    """
    if created:
        role_name_db = instance.role  # e.g., 'EDITOR'
        role_map = dict(USER_ROLES)
        group_name = role_map.get(role_name_db)  # example 'Editor'

        if group_name:
            try:
                # 1. Get the group using the correctly capitalized display name
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                group = Group.objects.create(name=group_name)
                # 2. Assign user to the group
                instance.groups.add(group)


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """
    Generates a Django REST Framework (DRF) API Token for every new user.

    **Trigger:** Runs after a ``User`` instance is created.

    :param sender: The model class (CustomUser).
    :param instance: The user instance.
    :param created: Boolean, True if this is a new user.
    """
    if created:
        Token.objects.create(user=instance)
        print(f"Created API Token for user: {instance.username}")
