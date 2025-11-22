# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# ***************************** forms.py *******************************

"""
forms.py
========

This module contains the Django forms used for user input, validation,
and data processing.

It includes:
    * **Authentication Forms:** Login and Registration.
    * **Role-Specific Registration:** handling distinct logic for Readers,
    Journalists, and Editors.
    * **Article Management:** Forms for creating, editing, and updating
    article status.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Publisher, Article


# 1. Login Form
class CustomLoginForm(AuthenticationForm):
    """
    A customized login form extending Django's built-in AuthenticationForm.

    Adds specific widgets and placeholders for better UX.
    """
    username = forms.CharField(
        label='User Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Username'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password'})
    )


# 2. Base Registration Form
class BaseUserRegistrationForm(UserCreationForm):
    """
    Base registration form for all user roles.

    Extends ``UserCreationForm`` to include email and profile photo fields,
    which are common across all roles (Reader, Journalist, Editor).

    :ivar email: Required email field.
    :ivar profile_photo: Optional image upload field.
    """
    email = forms.EmailField(
        required=True,
        label='Email Address',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter Email Address'})
    )
    profile_photo = forms.ImageField(
        required=False,
        label='Add Profile Photo'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'profile_photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['username'].label = 'User Name'
        if 'password2' in self.fields:
            self.fields['password2'].label = 'Confirm Password'


# 3. Role-Specific Forms
# A. Reader Registration
class ReaderRegistrationForm(BaseUserRegistrationForm):
    """Simple registration form for the Reader role."""
    pass


# B. Publisher Affiliation Mixin (For Journalist and Editor)
class PublisherAffiliationForm(BaseUserRegistrationForm):
    """
    A mixin/base form for staff roles (Journalist/Editor) that require
    Publisher affiliation.

    Handles the input of 'access passwords' to link a new user to a
    Publisher organization.

    :ivar actualtoday_password: Password field for joining 'ActualToday'.
    :ivar sporttoday_password: Password field for joining 'SportToday'.
    """
    actualtoday_password = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter ActualToday'
                                          ' Access Password'}),
        label='ActualToday Access Password'
    )
    sporttoday_password = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter SportToday'
                                          ' Access Password'}),
        label='SportToday Access Password'
    )

    def clean(self):
        """
        Custom validation logic to verify publisher passwords.

        Process:
            1. Checks if at least one password field is filled.
            2. Verifies the provided password against the stored
            ``Publisher`` record.
            3. If valid, adds the Publisher object to
            ``cleaned_data['publishers_to_join']``.

        :return: The cleaned data dictionary.
        :raises ValidationError: If no publisher is selected or if
        passwords are incorrect.
        """
        cleaned_data = super().clean()

        actualtoday_pass = cleaned_data.get('actualtoday_password')
        sporttoday_pass = cleaned_data.get('sporttoday_password')

        valid_publishers = []

        # 1. ENFORCE MINIMUM ONE PUBLISHER (Validation)
        if not actualtoday_pass and not sporttoday_pass:
            raise ValidationError(
                "Journalists and Editors must join at least one Publisher. "
                "Please provide a valid access password for ActualToday or "
                "SportToday."
            )

        # 2. CHECK AND COLLECT ActualToday PUBLISHER
        if actualtoday_pass:
            try:
                publisher_at = Publisher.objects.get(name='ActualToday')
                if publisher_at.access_password != actualtoday_pass:
                    # Password incorrect
                    self.add_error('actualtoday_password',
                                   "Incorrect access password for"
                                   " ActualToday.")
                else:
                    # Password correct: Add the Publisher object to the list
                    valid_publishers.append(publisher_at)
            except Publisher.DoesNotExist:
                self.add_error('actualtoday_password',
                               "ActualToday Publisher not found. Contact"
                               " administrator.")

        # 3. CHECK AND COLLECT SportToday PUBLISHER
        if sporttoday_pass:
            try:
                publisher_st = Publisher.objects.get(name='SportToday')
                if publisher_st.access_password != sporttoday_pass:
                    # Password incorrect
                    self.add_error('sporttoday_password',
                                   "Incorrect access password for SportToday.")
                else:
                    # Password correct: Add the Publisher object to the list
                    valid_publishers.append(publisher_st)
            except Publisher.DoesNotExist:
                self.add_error('sporttoday_password',
                               "SportToday Publisher not found. Contact"
                               " administrator.")

        # 4. ATTACH THE LIST OF VALID PUBLISHERS TO CLEANED_DATA
        cleaned_data['publishers_to_join'] = valid_publishers

        # 5. RETHROW ERRORS IF ANY VALIDATION FAILED
        if self.errors:
            raise ValidationError(self.errors)

        return cleaned_data


# C. Journalist Registration
class JournalistRegistrationForm(PublisherAffiliationForm):
    """Registration form for the Journalist role, inherits Publisher logic."""
    pass


# D. Editor Registration
class EditorRegistrationForm(PublisherAffiliationForm):
    """Registration form for the Editor role, inherits Publisher logic."""
    pass


# E. Article Management Forms
class ArticleForm(forms.ModelForm):
    """
    Form used by Journalists and Editors to create and edit articles.

    :ivar title: The headline of the article.
    :ivar body: The main text content.
    :ivar publisher: Dropdown to select which publisher this article
        belongs to.
    :ivar featured_image: Optional cover image.
    """

    class Meta:
        model = Article
        # Author and Editor will be assigned automatically in the view
        fields = ['title', 'body', 'publisher', 'featured_image']

        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter a '
                                     'compelling title'}),
            'body': forms.Textarea(attrs={'rows': 15, 'placeholder': 'Start'
                                   'writing your article here...'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and dynamically filters the 'publisher' field.

        Ensures that a Journalist can only submit articles to a Publisher they
        are actually affiliated with.

        :param author: The user instance (Journalist) passed from the view.
        """
        author = kwargs.pop('author', None)
        super().__init__(*args, **kwargs)
        # Check if the form instance has an author
        current_author = None
        if self.instance and self.instance.author:
            current_author = self.instance.author
        elif author:
            current_author = author

        # Filter the Publisher choices
        if current_author and current_author.publishers.exists():
            # Restrict choices to the publishers the author is affiliated with
            self.fields['publisher'].queryset = current_author.publishers.all()
        else:
            # If no author or no publishers are affiliated, the list is empty
            self.fields['publisher'].queryset = Publisher.objects.none()


class ArticleStatusUpdateForm(forms.ModelForm):
    """
    Form used by Editors to change the workflow status of an article.

    Typically used in the review dashboard.
    """

    class Meta:
        model = Article
        # Only the status field is directly exposed
        fields = ['status']
