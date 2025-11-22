# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# ***************************** views.py *******************************

"""
views.py
========

This module handles the request-response cycle for the DailyNews Application.

It organizes views into logical sections:
    1. **Authentication & Registration:** Login, Logout, and generic
        registration handlers.
    2. **Reader Views:** Public feeds, article reading, and subscriptions.
    3. **Journalist Views:** Dashboard, article creation, and editing.
    4. **Editor Views:** Dashboard, article review, and publishing.
    5. **Subscription Management:** Logic for following publishers and
        journalists.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib import messages
from django import forms

from .forms import (
    CustomLoginForm, ReaderRegistrationForm, JournalistRegistrationForm,
    EditorRegistrationForm, ArticleForm
)
from .models import (
    CustomUser, Publisher, Article, JournalistSubscription,
    PublisherSubscription
)


# ACCESS CONTROL HELPER FUNCTIONS

def is_reader(user):
    return user.role == 'READER'


def is_journalist(user):
    return user.role == 'JOURNALIST'


def is_editor(user):
    return user.role == 'EDITOR'


def is_publisher_staff(user):
    return user.role in ['JOURNALIST', 'EDITOR']


# 1. AUTHENTICATION & REGISTRATION VIEWS
def login_view(request):
    """
    Handles user login and redirects based on role or 'next' URL.

    If a 'next' parameter is present in the POST request, the user is
        redirected there.
    Otherwise, they are redirected to their role-specific dashboard.

    :param request: The HTTP request object.
    :return: Rendered login page or redirect to home.
    """

    # Define a default role-based redirect in case 'next' is not present
    def get_role_redirect_url(user):
        if is_journalist(user):
            return 'journalist_home'
        elif is_editor(user):
            return 'editor_home'
        else:
            return 'reader_home'

    if request.user.is_authenticated:
        return redirect(get_role_redirect_url(request.user))

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Check POST data first (from the hidden input in login.html)
            next_url = request.POST.get('next')

            if next_url:
                # Use the 'next' URL if it was provided
                return redirect(next_url)

            # If no 'next' URL, use role-based redirection
            return redirect(get_role_redirect_url(user))
    else:
        form = CustomLoginForm()

    return render(request, 'DailyNews_App/login.html', {'form': form})


# DailyNews_App/views.py (Modified article_list function)
def article_list(request):
    """
    Displays a global list of all published articles.

    Calculates subscription status for logged-in users to toggle UI buttons
    (Subscribe/Unsubscribe) efficiently.

    :param request: The HTTP request object.
    :return: Rendered 'article_list.html' with article data context.
    """

    # Fetch all PUBLISHED articles
    articles = Article.objects.filter(status='PUBLISHED').order_by(
        '-publication_date')

    article_data = []

    if request.user.is_authenticated:
        # Get IDs of all subscribed items as Python sets (fast lookup)
        subscribed_journalists = set(
            request.user.reader_journalist_subs.values_list(
                'journalist__pk', flat=True))
        subscribed_publishers = set(
            request.user.reader_publisher_subs.values_list(
                'publisher__pk', flat=True))

        for article in articles:
            # Calculate subscription status for each article in Python
            is_subbed_j = article.author.pk in subscribed_journalists
            is_subbed_p = article.publisher.pk in \
                subscribed_publishers if article.publisher else False

            # Create a dictionary to hold article and its status flags
            article_data.append({
                'article': article,
                'is_subbed_j': is_subbed_j,
                'is_subbed_p': is_subbed_p,
            })
    else:
        # If not authenticated, just pass the articles directly
        article_data = [{'article': article} for article in articles]

    context = {
        'article_data': article_data,
    }

    return render(request, 'DailyNews_App/article_list.html', context)


@login_required
def toggle_subscription(request):
    """
    Handles POST requests to subscribe/unsubscribe to journalists or
    publishers.

    :param request: The HTTP request object (must be POST).
    :return: Redirects back to 'article_list'.
    """
    if request.method == 'POST':
        user = request.user
        item_id = request.POST.get('item_id')
        item_type = request.POST.get('item_type')

        if not item_id or item_type not in ['journalist', 'publisher']:
            messages.error(request, "Invalid subscription request.")
            return redirect('article_list')

        try:
            if item_type == 'journalist':
                journalist = get_object_or_404(CustomUser, pk=item_id)
                # Ensure the user being subscribed to is actually a journalist
                if journalist.role != 'JOURNALIST':
                    messages.error(request, "Cannot subscribe to this user "
                                   "role.")
                    return redirect('article_list')

                sub, created = JournalistSubscription.objects.get_or_create(
                    reader=user, journalist=journalist
                )
                if created:
                    messages.success(request, f"Successfully subscribed "
                                     f"to {journalist.username}!")
                else:
                    sub.delete()
                    messages.warning(request, f"Unsubscribed "
                                     f"from {journalist.username}.")

            elif item_type == 'publisher':
                publisher = get_object_or_404(Publisher, pk=item_id)
                sub, created = PublisherSubscription.objects.get_or_create(
                    reader=user, publisher=publisher
                )
                if created:
                    messages.success(request, f"Successfully subscribed "
                                     f"to {publisher.name}!")
                else:
                    sub.delete()
                    messages.warning(request, f"Unsubscribed "
                                     f"from {publisher.name}.")

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    # Redirect back to the article list page
    return redirect('article_list')


@login_required
def logout_view(request):
    """
    Logs out the current user and redirects to the login page.

    :param request: The HTTP request object.
    """
    logout(request)
    return redirect('login')


def register_select_role(request):
    """Initial registration view to select user role."""
    return render(request, 'DailyNews_App/register.html')


def register_user(request, role_name, form_class, template_name,
                  redirect_name):
    """
    Generic helper view to handle registration for different user roles.

    Processes the form, assigns the role, handles implicit publisher affiliation
    (for Editors), logs the user in, and redirects to their specific home page.

    :param request: The HTTP request object.
    :param role_name: String role ('READER', 'JOURNALIST', 'EDITOR').
    :param form_class: The Django form class to use for validation.
    :param template_name: The name of the template to render.
    :param redirect_name: The URL name to redirect to upon success.
    :return: Rendered template or redirect.
    """
    if request.method == 'POST':
        # CRITICAL FIX 1: Pass request.FILES to handle profile picture upload
        form = form_class(request.POST, request.FILES)

        if form.is_valid():
            user = form.save(commit=False)
            user.role = role_name

            publishers_to_join = form.cleaned_data.get(
                'publishers_to_join', [])

            # FIX 2: Publisher Affiliation (Implicit Selection via Password)
            # The form's clean() method stores the Publisher object under the
            # key 'publisher_to_join'. We retrieve that validated object here.
            if role_name == 'EDITOR' and len(publishers_to_join) > 1:
                messages.error(
                    request, "As an Editor, you can only join one publisher.")
                return render(request, f'DailyNews_App/{template_name}.html',
                              {'form': form})

            user.save()

            if publishers_to_join:
                user.publishers.set(publishers_to_join)

            # LOG THE USER IN
            login(request, user)

            # This ensures only the welcome message is displayed.
            messages.success(request, f"Welcome to Daily News! You are "
                             f"registered as a {role_name.title()}.")

            return redirect(redirect_name)

        else:  # Validation failed
            pass

    else:  # GET request
        form = form_class()

    # Final render for GET request or failed POST request
    return render(request, f'DailyNews_App/{template_name}.html',
                  {'form': form})


def register_reader(request):
    return register_user(
        request, 'READER', ReaderRegistrationForm, 'register_reader',
        'reader_home'
    )


def register_journalist(request):
    return register_user(
        request, 'JOURNALIST', JournalistRegistrationForm,
        'register_journalist', 'journalist_home'
    )


def register_editor(request):
    """Handles the registration of a new Editor user using the generic
    handler."""
    return register_user(
        request, 'EDITOR', EditorRegistrationForm,
        'register_editor', 'editor_home'
    )


# 2. READER/PUBLIC VIEWS
@login_required
@user_passes_test(is_reader, login_url='/login/')
def reader_home(request):
    """
    Displays the personalized news feed for a Reader.

    Aggregates articles from:
        1. Subscribed Journalists.
        2. Subscribed Publishers.
        3. A general feed of all published articles (excluding duplicates).

    Also provides sidebar data for current subscriptions.

    :param request: The HTTP request object.
    :return: Rendered 'reader_home.html'.
    """

    # 1. Get articles from subscribed sources
    subscribed_journalists = request.user.reader_journalist_subs.\
        values_list('journalist__pk', flat=True)
    subscribed_publishers = request.user.reader_publisher_subs.\
        values_list('publisher__pk', flat=True)

    # 1. Get articles from subscribed sources
    subscribed_journalists = request.user.reader_journalist_subs.\
        values_list('journalist__pk', flat=True)
    subscribed_publishers = request.user.reader_publisher_subs.\
        values_list('publisher__pk', flat=True)

    # Filter for articles that are PUBLISHED AND match a subscription
    subscribed_feed = Article.objects.filter(status='PUBLISHED').filter(
        Q(author__pk__in=subscribed_journalists) |
        Q(publisher_id__in=subscribed_publishers)
    ).order_by('-publication_date')
    # 2. General Feed (All Published Articles) - Used as fallback/supplement
    general_feed = Article.objects.filter(status='PUBLISHED'). \
        order_by('-publication_date').exclude(
        pk__in=subscribed_feed.values_list('pk', flat=True)
    )

    # 3. Sidebar Subscriptions List (Annotated with published article count)
    journalist_subs = CustomUser.objects.\
        filter(pk__in=subscribed_journalists).annotate(
            article_count=Count('written_articles',
                                filter=Q(written_articles__status='PUBLISHED'))
                )
    publisher_subs = Publisher.objects.filter(pk__in=subscribed_publishers) \
        .annotate(article_count=Count('articles',
                                      filter=Q(articles__status='PUBLISHED'))
                  )

    context = {
        # Combine subscribed feed and general feed
        'article_feed': list(subscribed_feed) + list(general_feed),
        'journalist_subs': journalist_subs,
        'publisher_subs': publisher_subs,
    }
    return render(request, 'DailyNews_App/reader_home.html', context)


@login_required
@user_passes_test(is_reader, login_url='/login/')
def article_reader(request, pk):
    """
    Displays a single article detail view for a Reader.

    Enforces that the article must be 'PUBLISHED' unless the user is staff.
    Also displays 'More from this author'.

    :param request: The HTTP request object.
    :param pk: Primary Key of the article.
    :return: Rendered 'article_reader.html'.
    """
    article = get_object_or_404(Article, pk=pk)

    # Only allow viewing if the article is PUBLISHED
    if article.status != 'PUBLISHED':
        # Redirect based on user role if they try to access a non-published
        # article
        if request.user.role == 'JOURNALIST':
            return redirect('journalist_home')
        elif request.user.role == 'EDITOR':
            return redirect('editor_home')
        else:  # READER or general user
            messages.error(
                request, "This article is not yet available for reading.")
            return redirect('article_list')

    # Check if the user is subscribed to the author
    is_subscribed = JournalistSubscription.objects.filter(
        reader=request.user, journalist=article.author
    ).exists()

    # Get more articles from the same author
    more_articles = Article.objects.filter(
        author=article.author, status='PUBLISHED'
    ).exclude(pk=pk).order_by('-publication_date')[:3]

    context = {
        'article': article,
        'is_subscribed': is_subscribed,
        'more_articles': more_articles,
    }
    return render(request, 'DailyNews_App/article_reader.html', context)


@login_required
@user_passes_test(is_reader, login_url='/login/')
def journalist_profile(request, pk):
    """
    Displays a public profile for a Journalist.

    :param request: The HTTP request object.
    :param pk: Primary Key of the Journalist (CustomUser).
    :return: Rendered 'journalist_profile.html'.
    """
    journalist = get_object_or_404(CustomUser, pk=pk, role='Journalist')

    # Published articles by this journalist
    published_articles = Article.objects.filter(
        author=journalist, status='PUBLISHED'
    ).order_by('-publication_date')

    # Check if the current reader is subscribed
    is_subscribed = JournalistSubscription.objects.filter(
        reader=request.user, journalist=journalist
    ).exists()

    # Calculate stats
    journalist.article_count = published_articles.count()
    journalist.subscriber_count = journalist.followers.count()

    context = {
        'journalist': journalist,
        'published_articles': published_articles,
        'is_subscribed': is_subscribed,
    }
    return render(request, 'DailyNews_App/journalist_profile.html', context)


@login_required
@user_passes_test(is_reader, login_url='/login/')
def publisher_profile(request, pk):
    """
    Displays a public profile for a Publisher.

    :param request: The HTTP request object.
    :param pk: Primary Key of the Publisher.
    :return: Rendered 'publisher_profile.html'.
    """
    publisher = get_object_or_404(Publisher, pk=pk)

    # Published articles by this publisher
    published_articles = Article.objects.filter(
        publisher=publisher, status='PUBLISHED'
    ).order_by('-publication_date')

    # Calculate stats
    publisher.article_count = published_articles.count()
    publisher.journalist_count = CustomUser.objects.filter(
        publishers=publisher, role='JOURNALIST'
    ).count()

    publisher.subscriber_count = PublisherSubscription.objects.filter(
        publisher=publisher
    ).count()

    context = {
        'publisher': publisher,
        'published_articles': published_articles,
    }
    return render(request, 'DailyNews_App/publisher_profile.html', context)


# 3. JOURNALIST VIEWS
@login_required
@user_passes_test(is_journalist, login_url='/login/')
def journalist_home(request):
    """Journalist dashboard showing their articles grouped by status."""
    journalist_articles = Article.objects.filter(author=request.user).\
        order_by('-last_edited_date')

    context = {
        'journalist_articles': journalist_articles,
        'drafts': journalist_articles.filter(status='DRAFT'),
        'awaiting_review': journalist_articles.filter(
            status='AWAITING_REVIEW'),
        'published': journalist_articles.filter(status='PUBLISHED'),
        'rejected': journalist_articles.filter(status='REJECTED'),
    }
    return render(request, 'DailyNews_App/journalist_home.html', context)


@login_required
@user_passes_test(is_journalist)
def article_create_edit(request, pk=None):
    """
    Handles creating and editing of articles by Journalists, allowing selection
    of which affiliated publisher to submit to.
    """

    # Get ALL affiliated publishers
    affiliated_publishers = request.user.publishers.all()
    has_publisher = affiliated_publishers.exists()

    # 1. SETUP: Fetch or Initialize Article (Standard logic)
    if pk:
        article = get_object_or_404(Article, pk=pk)
        title = "Edit Article"

        if article.author != request.user:
            messages.error(
                request, "You do not have permission to edit this article.")
            return redirect('journalist_home')

        FORBIDDEN_EDIT_STATUSES = ['PUBLISHED', 'REJECTED', 'AWAITING_REVIEW']

        if article.status in FORBIDDEN_EDIT_STATUSES:
            messages.warning(
                request, f"Article '{article.title}' cannot be edited because "
                f"its status is '{article.get_status_display()}' and is "
                f"considered finalized or pending editor action.")
            return redirect('journalist_home')

    else:
        article = Article(author=request.user, publisher=None)
        title = "Create New Article"

    # 2. POST REQUEST HANDLING
    if request.method == 'POST':
        post_data = request.POST.copy()
        action = post_data.get('action', 'draft')

        article_publisher = None
        new_status = 'DRAFT'  # Default status

        if action == 'publish_independent':
            new_status = 'PUBLISHED'
            article_publisher = None  # Independent articles have no publisher

        elif action == 'submit_publisher':
            publisher_id = request.POST.get('publisher_to_submit')

            if publisher_id:
                try:
                    # Look up the selected publisher, ensuring the journalist
                    # is affiliated
                    selected_publisher = affiliated_publishers.get(
                        pk=publisher_id)
                    new_status = 'AWAITING_REVIEW'
                    article_publisher = selected_publisher
                except affiliated_publishers.model.DoesNotExist:
                    messages.error(request, "Invalid publisher selected.")
                    new_status = 'DRAFT'
            else:
                # If they hit 'Submit for Review' but didn't select a publisher
                messages.error(
                    request, "Please select a publisher for review.")
                new_status = 'DRAFT'

        else:
            # Covers 'draft' action or invalid submission. Keep existing
            # publisher if editing.
            article_publisher = article.publisher

        post_data['status'] = new_status

        form = ArticleForm(post_data, request.FILES, instance=article)

        if form.is_valid():
            new_article = form.save(commit=False)

            new_article.status = new_status
            new_article.publisher = article_publisher

            if new_status == 'PUBLISHED':
                new_article.publication_date = timezone.now()

            new_article.author = request.user
            new_article.last_edited_date = timezone.now()

            new_article.save()

            # Success message and redirect
            if new_article.status == 'PUBLISHED':
                messages.success(request, f"Article '{new_article.title}' "
                                 f"published successfully!")
            elif new_article.status == 'AWAITING_REVIEW':
                publisher_name = (
                    article_publisher.name if article_publisher else "a "
                    "publisher"
                )
                messages.success(request, f"Article '{new_article.title}' "
                                 f"submitted to {publisher_name} for review.")
            else:
                messages.info(request, f"Article '{new_article.title}' saved "
                              f"as a draft.")

            return redirect('journalist_home')

        else:
            messages.error(request, "Error saving article. Please correct the "
                           "fields below.")
            form = ArticleForm(request.POST, request.FILES, instance=article)

    # 4. GET REQUEST / FAILED VALIDATION RENDERING
    else:
        form = ArticleForm(instance=article)

    context = {
        'form': form,
        'title': title,
        'is_new': pk is None,
        'article': article if pk else None,
        'is_editing': pk is not None,
        'affiliated_publishers': affiliated_publishers,
        'has_publisher': has_publisher
    }
    return render(request, 'DailyNews_App/article_create_edit.html', context)


# DailyNews_App/views.py (Inside article_delete function)

# DailyNews_App/views.py (Replace the existing article_delete function)

@login_required
@user_passes_test(is_publisher_staff)
def article_delete(request, pk):
    """Allows a journalist or affiliated editor to delete an article."""

    article = get_object_or_404(Article, pk=pk)
    user_role = request.user.role

    # Determine the appropriate redirect URL based on the user's role
    default_redirect_url = (
        'editor_home' if user_role == 'EDITOR' else 'journalist_home'
    )
    # 1. Permission Check: Must be the author OR an affiliated editor
    is_author = article.author == request.user
    is_affiliated_editor = user_role == 'EDITOR' and \
        article.publisher in request.user.publishers.all()

    if not (is_author or is_affiliated_editor):
        messages.error(
            request, "You do not have permission to delete this article.")
        return redirect(default_redirect_url)

    # 2. Only allow deletion of non-finalized articles
    ALLOW_DELETION_STATUSES = ['DRAFT', 'REVISION', 'AWAITING_REVIEW']

    if article.status not in ALLOW_DELETION_STATUSES:
        messages.warning(request,
                         f"Article '{article.title}' cannot be deleted because"
                         f" its status is '{article.get_status_display()}' "
                         f"and is considered finalized.")
        return redirect(default_redirect_url)

    context = {
        'article': article
    }

    # 3. Handle POST request (Deletion confirmation)
    if request.method == 'POST':
        article_title = article.title
        article.delete()
        messages.success(request, f"Article '{article_title}' was "
                         f"successfully deleted.")
        return redirect('editor_home')

    # 4. Handle GET request (Render confirmation page)
    return render(
        request, 'DailyNews_App/article_delete_confirm.html', context)


@login_required
@user_passes_test(is_journalist, login_url='/login/')
def article_journalist(request, pk):
    """Journalist view of their own article."""
    article = get_object_or_404(Article, pk=pk, author=request.user)

    if request.method == 'POST' and 'delete' in request.POST:
        article.delete()
        messages.success(request, f"Article '{article.title}' deleted"
                         f"successfully.")
        return redirect('journalist_home')

    context = {
        'article': article,
    }
    return render(request, 'DailyNews_App/article_journalist.html', context)


# 4. EDITOR VIEWS
@login_required
@user_passes_test(is_editor, login_url='/login/')
def editor_home(request):
    """Editor dashboard showing articles awaiting review from their
    publisher."""
    affiliated_publishers = request.user.publishers.all()

    if not affiliated_publishers:
        articles_to_review = Article.objects.none()
    else:
        articles_to_review = Article.objects.filter(
            publisher__in=affiliated_publishers,
            status='AWAITING_REVIEW'
        ).order_by('-creation_date')

    context = {
        'articles_to_review': articles_to_review,
        'publishers': affiliated_publishers,
    }
    return render(request, 'DailyNews_App/editor_home.html', context)


@login_required
@user_passes_test(is_editor, login_url='/login/')
def article_editor(request, pk):
    """Editor review page allowing content editing, publish, or delete."""
    article = get_object_or_404(Article, pk=pk)

    # 1. Access Control Check
    if article.publisher not in request.user.publishers.all():
        return HttpResponseForbidden("You do not have permission to review "
                                     "this article.")

    if request.method == 'POST':
        action = request.POST.get('action')  # Get the action from the button

        # 2. HANDLE DELETION (Direct action, no form validation needed)
        if action == 'delete':
            article_title = article.title
            article.delete()
            messages.success(request, f"Article '{article_title}' was "
                             f"deleted.")
            return redirect('editor_home')

        # 3. HANDLE CONTENT EDIT & STATUS CHANGE (Requires ArticleForm)
        form = ArticleForm(request.POST, request.FILES, instance=article)

        if form.is_valid():
            article = form.save(commit=False)
            article.last_edited_date = timezone.now()
            article.editor = request.user  # Assign the reviewing editor

            # 4. HANDLE STATUS CHANGE (ONLY PUBLISH is allowed)
            if action == 'publish':
                article.status = 'PUBLISHED'
                article.publication_date = timezone.now()

                if not article.publisher:
                    editor_primary_publisher = request.user.publishers.first()

                    if editor_primary_publisher:
                        # Assign the article to the editor's primary publisher
                        article.publisher = editor_primary_publisher
                    else:
                        messages.error(
                            request, "Cannot publish: Article has no publisher"
                            " and you are not affiliated with one.")
                        # Prevent saving and return to the edit page
                        return redirect('article_editor', pk=article.pk)

                messages.success(request, f"Article '{article.title}' "
                                 f"published successfully!")

            else:
                # This covers the 'save' action.
                messages.info(request, f"Article '{article.title}' content "
                              f"edits saved.")

            article.save()
            return redirect('editor_home')

        else:
            # If form validation fails, proceed to render with errors
            messages.error(request, "Error saving article content. Please "
                           "correct the fields.")

    # --- HANDLE GET REQUEST ---
    else:
        # Use the full ArticleForm to display the article content for editing
        form = ArticleForm(instance=article)

    context = {
        'article': article,
        'form': form,
    }
    return render(request, 'DailyNews_App/article_editor.html', context)


# --- 5. SUBSCRIPTION VIEWS ---
@login_required
@user_passes_test(is_reader, login_url='/login/')
def subscribe_journalist(request, pk):
    """Toggles subscription status for a journalist."""
    journalist = get_object_or_404(CustomUser, pk=pk, role='JOURNALIST')

    # Check if already subscribed
    subscription, created = JournalistSubscription.objects.get_or_create(
        reader=request.user, journalist=journalist
    )

    if created:
        messages.success(request, f"You are now subscribed to "
                         f"{journalist.username}!")
    else:
        # If it exists, delete it (unsubscribe)
        subscription.delete()
        messages.info(request, f"You have unsubscribed from "
                      f"{journalist.username}.")

    # Redirect back to the page where the action was initiated
    return redirect(request.META.get('HTTP_REFERER', 'reader_home'))


@login_required
@user_passes_test(is_reader, login_url='/login/')
def subscribe_publisher(request, pk):
    """Toggles subscription status for a publisher."""
    publisher = get_object_or_404(Publisher, pk=pk)

    # Check if already subscribed
    subscription, created = PublisherSubscription.objects.get_or_create(
        reader=request.user, publisher=publisher
    )

    if created:
        messages.success(request, f"You are now subscribed to "
                         f"{publisher.name}!")
    else:
        # If it exists, delete it (unsubscribe)
        subscription.delete()
        messages.info(request, f"You have unsubscribed from {publisher.name}.")

    return redirect(request.META.get('HTTP_REFERER', 'reader_home'))


@login_required
def manage_subscriptions_view(request):
    """
    Placeholder view for the subscription management page.
    This view must be created to resolve the NoReverseMatch error.
    """

    context = {}
    return render(request, 'manage_subscriptions.html', context)


# 6. PROFILE VIEW (Account Management)
@login_required
def profile_view(request):
    """Allows user to update their personal details."""
    user = request.user

    # NOTE: We use a simplified ModelForm here for profile updates.
    class ProfileUpdateForm(forms.ModelForm):
        class Meta:
            model = CustomUser
            fields = ['first_name', 'last_name', 'email', 'profile_photo']

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated"
                             "successfully.")
            return redirect('profile_view')
    else:
        form = ProfileUpdateForm(instance=user)

    context = {
        'form': form,
    }
    return render(request, 'DailyNews_App/profile.html', context)
