from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Publisher, CustomUser, Article


# 1. Define Custom Admin Class for CustomUser
class CustomUserAdmin(UserAdmin):
    # Add 'role', 'publishers', and 'profile_photo' to the fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Affiliation', {'fields': ('role', 'publishers',
                                           'profile_photo')}),
    )

    # Add 'role' to the list displayed in the changelist view
    list_display = UserAdmin.list_display + ('role',)

    # Customize search or filter fields
    filter_horizontal = ('publishers',)


# 2. Register the models
# Unregister the old simple registration (if it exists)
try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass

# Register necessary models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Publisher)
admin.site.register(Article)
