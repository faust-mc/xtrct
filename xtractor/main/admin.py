from django.contrib import admin
from .models import ComponentType, FormObject, HeaderObjects, RowObjects, FieldObject, FormName, Pages, Extraction
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Permission


admin.site.register([ComponentType, FormObject, HeaderObjects, RowObjects, FieldObject, Pages, Extraction])


class FormNameInline(admin.TabularInline):
    model = FormName.allowed_users.through   # the through table
    extra = 1


class CustomUserAdmin(BaseUserAdmin):
    inlines = [FormNameInline]

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        # Limit the user_permissions field to only custom permissions
        if db_field.name == "user_permissions":
            kwargs["queryset"] = Permission.objects.filter(codename__startswith="access_")
        return super().formfield_for_manytomany(db_field, request, **kwargs)


# Unregister default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Keep FormName admin
@admin.register(FormName)
class FormNameAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_by")
    search_fields = ("name",)
