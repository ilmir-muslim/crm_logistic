from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"
    extra = 1 
    max_num = 1  

    def get_formset(self, request, obj=None, **kwargs):
        if obj is None:
            self.extra = 0
        else:
            self.extra = 1
        return super().get_formset(request, obj, **kwargs)


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
