# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# ***************************** models.py ******************************

"""
models.py
=========

This module defines the database structure for the DailyNews application.

It includes models for:
    * User management with specific roles (Reader, Journalist, Editor).
    * Publisher organizations.
    * Article content management and workflow.
    * Subscription relationships between readers, publishers, and journalists.
"""

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- Role Definitions ---
USER_ROLES = (
    ('READER', 'Reader'),
    ('JOURNALIST', 'Journalist'),
    ('EDITOR', 'Editor'),
)


# --- 1. PUBLISHER MODEL ---
class Publisher(models.Model):
    """
    Represents a news organization that employs Editors and Journalists
    and publishes Articles.

    :ivar name: The unique name of the publisher.
    :ivar description: A text description of the publisher.
    :ivar access_password: A specific code used during registration to
        link staff to this publisher.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # This is a placeholder for the secret password mentioned in the
    # registration process
    access_password = models.CharField(max_length=128,
                                       verbose_name="Publisher Join Password")

    @staticmethod
    def ensure_publishers_exist():
        """Creates the two required Publishers if they do not exist."""

        publishers_to_create = {
            'ActualToday': 'ActualToday',
            'SportToday': 'SportToday',
        }

        for name, password in publishers_to_create.items():
            # Use get_or_create to only create if it doesn't already exist
            Publisher.objects.get_or_create(
                name=name,
                defaults={
                    'description': f'Core news outlet: {name}',
                    'access_password': password
                }
            )

    def __str__(self):
        return self.name


# --- 2. CUSTOM USER MODEL ---
class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Includes role-based fields and subscription relationships.

    :ivar role: The user's role in the system (Reader, Journalist, or Editor).
    :ivar publisher_subscriptions: M2M relationship to Publishers a Reader
        follows.
    :ivar journalist_subscriptions: M2M relationship to Journalists a Reader
        follows.
    :ivar publishers: M2M relationship indicating which Publishers employ this
        user (for staff).
    :ivar profile_photo: Optional profile image for the user.
    """
    role = models.CharField(max_length=10, choices=USER_ROLES,
                            default='Reader')

    # Subscriptions to Publishers (Reader Field 1)
    publisher_subscriptions = models.ManyToManyField(
        Publisher,
        through='PublisherSubscription',
        related_name='subscribing_readers',
        blank=True
    )

    # Subscriptions to Journalists (Reader Field 2) - M2M self-referential
    journalist_subscriptions = models.ManyToManyField(
        'self',
        through='JournalistSubscription',
        symmetrical=False,
        related_name='followers',
        blank=True
    )

    # Many users (Journalists/Editors) can belong to one Publisher
    publishers = models.ManyToManyField(
        Publisher,
        related_name='staff',
        blank=True
    )

    profile_photo = models.ImageField(upload_to='profile_pics/',
                                      null=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=('The groups this user belongs to. A user will get all'
                   ' permissions granted to each of their groups.'),
        related_name='dailynews_custom_user_set',
        related_query_name='user',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name='dailynews_custom_user_permissions',
        related_query_name='user',
    )

    def __str__(self):
        return self.username


# --- 3. SUBSCRIPTION MODELS ---
class PublisherSubscription(models.Model):
    """
    Intermediary model representing a Reader's subscription to a Publisher.

    :ivar reader: The CustomUser (Reader) who is subscribing.
    :ivar publisher: The Publisher being subscribed to.
    :ivar date_subscribed: Timestamp of when the subscription was created.
    """
    reader = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               related_name='reader_publisher_subs')
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reader', 'publisher')


class JournalistSubscription(models.Model):
    """
    Intermediary model representing a Reader's subscription to a Journalist.

    :ivar reader: The CustomUser (Reader) who is subscribing.
    :ivar journalist: The CustomUser (Journalist) being subscribed to.
    :ivar date_subscribed: Timestamp of when the subscription was created.
    """
    reader = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               related_name='reader_journalist_subs')
    journalist = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                   related_name='journalist_followers')
    date_subscribed = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reader', 'journalist')

    permissions = [
            ("subscribe_article", "Can subscribe to content creators or"
             "publishers"),
        ]


# --- 4. ARTICLE MODEL ---

class Article(models.Model):
    """
    Represents a news article within the application.

    :ivar title: The headline of the article.
    :ivar body: The main content of the article.
    :ivar creation_date: Automatically set when created.
    :ivar last_edited_date: Automatically updated on save.
    :ivar publication_date: Set automatically when status becomes 'PUBLISHED'.
    :ivar publisher: The Publisher organization this article belongs to.
    :ivar author: The Journalist who wrote the article.
    :ivar editor: The Editor who reviewed the article.
    :ivar status: The current workflow state (Draft, Awaiting Review, Rejected,
        Published).
    :ivar is_approved: Boolean flag, automatically True if status is Published.
    :ivar featured_image: Main image for the article.
    """

    # Status Choices
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('AWAITING_REVIEW', 'Awaiting Editor Review'),
        ('REJECTED', 'Rejected'),
        ('PUBLISHED', 'Published'),
    )

    title = models.CharField(max_length=255)
    body = models.TextField()

    # Article Metadata
    creation_date = models.DateTimeField(auto_now_add=True)
    last_edited_date = models.DateTimeField(auto_now=True)
    publication_date = models.DateTimeField(null=True, blank=True)

    # Relationship to Publisher and Author
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE,
                                  related_name='articles', null=True,
                                  blank=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               related_name='written_articles')
    editor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                               related_name='reviewed_articles',
                               null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='DRAFT')
    is_approved = models.BooleanField(default=False)

    # Image/Media
    featured_image = models.ImageField(upload_to='article_images/', null=True,
                                       blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to handle automatic approval logic.

        If the status is set to 'PUBLISHED', ``is_approved`` is set to True
        and ``publication_date`` is set to the current time (if not already 
        set). Otherwise, ``is_approved`` is set to False.

        :param args: Positional arguments passed to save.
        :param kwargs: Keyword arguments passed to save.
        """
        # Automatically set is_approved if status is PUBLISHED
        if self.status == 'PUBLISHED':
            self.is_approved = True
            if not self.publication_date:
                from django.utils import timezone
                self.publication_date = timezone.now()
        else:
            self.is_approved = False
        super().save(*args, **kwargs)

    class Meta:
        # Define the custom permission used by your signal for the Editor group
        permissions = [
            ("publish_article", "Can formally approve and publish an article"),
        ]


# --- 5. SIGNAL FOR PERMISSION ASSIGNMENT ---
@receiver(post_save, sender=CustomUser)
def assign_user_to_group(sender, instance, created, **kwargs):
    """
    Signal receiver to automatically assign users to groups based on their
    selected role.

    Triggered after a ``CustomUser`` is saved.

    :param sender: The model class (CustomUser).
    :param instance: The actual instance being saved.
    :param created: Boolean, True if a new record was created.
    :param kwargs: Additional keyword arguments.
    """
    if created:
        role_name = instance.role

        # 1. Add User to the correct Group
        try:
            group = Group.objects.get(name=role_name)
        except Group.DoesNotExist:
            # If the group doesn't exist, create it
            group = Group.objects.create(name=role_name)

            # --- Get Article Model Permissions ---
            article_content_type = ContentType.objects.get_for_model(Article)
            article_permissions = Permission.objects.filter(
                content_type=article_content_type)

            if role_name == 'Reader':
                # Reader: Can only view articles and newsletters.
                view_article_perm = Permission.objects.get(
                    codename='view_article')
                group.permissions.add(view_article_perm)

            elif role_name == 'Editor':
                # Editor: Can view, update, and delete articles
                perms_to_add = article_permissions.filter(codename__in=[
                    'view_article', 'change_article', 'delete_article'])
                group.permissions.set(perms_to_add)

            elif role_name == 'Journalist':
                # Journalist: Can create, view, update, and delete articles.
                perms_to_add = article_permissions.filter(codename__in=[
                    'add_article', 'view_article', 'change_article',
                    'delete_article'])
                group.permissions.set(perms_to_add)

            group.save()

        instance.groups.add(group)


# Import ContentType at the end to prevent circular dependency issues
from django.contrib.contenttypes.models import ContentType
