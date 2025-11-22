# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# ***************************** forms.py *******************************

# This file contains the forms for the DailyNews_App application

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Publisher, Article


# 1. Login Form
class CustomLoginForm(AuthenticationForm):
    """A simple form based on Django's built-in AuthenticationForm for
    user login."""
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
    Base form for all user roles, handling fields common to CustomUser
    like username, email, and password management.
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
    Form that adds specific fields for the two required publishers,
    handles validation, and ensures at least one publisher is joined.
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
        Custom validation to verify publisher join passwords and collect all
        valid Publisher objects for Many-to-Many assignment.
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
    """Form used by Journalists to create and edit articles."""

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
    Form used by Editors in article_editor.html to change the status
    and provide optional notes/feedback.
    """

    class Meta:
        model = Article
        # Only the status field is directly exposed
        fields = ['status']
