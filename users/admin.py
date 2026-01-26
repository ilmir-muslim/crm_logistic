from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import CustomUserCreationForm  


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"
    extra = 0
    max_num = 1

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj is None:
            formset.extra = 1
        return formset


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    add_form = CustomUserCreationForm  

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "email",
                    "first_name",
                    "last_name",
                ),
            },
        ),
    )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
