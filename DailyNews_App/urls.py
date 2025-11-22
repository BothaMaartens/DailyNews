# ************ M06T08 – Capstone Project – News Application ************

# *************************** Practical Task ***************************

# ***************************** urls.py ********************************

# This file contains the urls paths to connect the views logic and the
# App frontend.


from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
     # --- Auth Views (login/registration) ---
     path('login/', views.login_view, name='login'),
     path('register/', views.register_select_role,
          name='register_role_select'),
     path('register/reader/', views.register_reader, name='register_reader'),
     path('register/journalist/', views.register_journalist,
          name='register_journalist'),
     path('register/editor/', views.register_editor, name='register_editor'),
     path('logout/', views.logout_view, name='logout'),

     # --- Password Reset Views ---
     # 1. Form to request password reset email
     path('password_reset/',
          auth_views.PasswordResetView.as_view(
              template_name='auth/password_reset_form.html',
              # The email content is generated from this template
              email_template_name='auth/password_reset_email.html',
              success_url='/password_reset/done/'
          ),
          name='password_reset'),

     # 2. Confirmation that the reset email has been sent
     path('password_reset/done/',
          auth_views.PasswordResetDoneView.as_view(
              template_name='auth/password_reset_done.html'
          ),
          name='password_reset_done'),

     # 3. Link with token (where user enters new password)
     path('reset/<uidb64>/<token>/',
          auth_views.PasswordResetConfirmView.as_view(
              template_name='auth/password_reset_confirm.html',
              success_url='/reset/done/'
          ),
          name='password_reset_confirm'),

     # 4. Confirmation that the password has been successfully changed
     path('reset/done/',
          auth_views.PasswordResetCompleteView.as_view(
              template_name='auth/password_reset_complete.html'
          ),
          name='password_reset_complete'),

     # --- Reader/Public Views ---
     path('', views.reader_home, name='reader_home'),
     path('article/<int:pk>/', views.article_reader, name='article_reader'),
     path('journalist/<int:pk>/', views.journalist_profile,
          name='journalist_profile'),
     path('publisher/<int:pk>/', views.publisher_profile,
          name='publisher_profile'),
     path('subscriptions/manage/', views.manage_subscriptions_view,
          name='manage_subscriptions'),

     # --- Journalist Views ---
     path('journalist/dashboard/', views.journalist_home,
          name='journalist_home'),
     path('article/create/', views.article_create_edit, name='article_create'),
     path('article/edit/<int:pk>/', views.article_create_edit,
          name='article_edit'),
     path('article/view/journalist/<int:pk>/', views.article_journalist,
          name='article_journalist_view'),
     path('article/delete/<int:pk>/', views.article_delete,
          name='article_delete'),

     # --- Editor Views ---
     path('editor/dashboard/', views.editor_home, name='editor_home'),
     path('article/review/<int:pk>/', views.article_editor,
          name='article_editor_review'),

     # --- Utility Views ---
     path('subscribe/journalist/<int:pk>/', views.subscribe_journalist,
          name='subscribe_journalist'),
     path('subscribe/publisher/<int:pk>/', views.subscribe_publisher,
          name='subscribe_publisher'),

     # --- API Endpoints ---
     path('api/', include('DailyNews_App.api_urls')),

     # --- Profile View ---
     path('profile/', views.profile_view, name='profile_view'),

     # New universal article list feed and subscription toggle
     path('articles/', views.article_list, name='article_list'),
     path('subscribe/toggle/', views.toggle_subscription,
          name='toggle_subscription'),
]
