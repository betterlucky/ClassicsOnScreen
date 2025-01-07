from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from blog.models import Film, Comment, Show, Location, SiteUser


# Inline configuration for shows created by a user
class ShowInline(admin.TabularInline):
    model = Show
    extra = 0
    fields = ('film', 'location', 'eventtime', 'created_on')
    readonly_fields = ('created_on',)


# Admin configuration for SiteUser
@admin.register(SiteUser)
class SiteUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'credits', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'credits')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    inlines = [ShowInline]

    # Ensure credits are editable in the admin panel
    def get_readonly_fields(self, request, obj=None):
        """Override this method to make 'credits' editable."""
        readonly_fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields += ('credits',)  # Only superusers can edit credits
        return readonly_fields


# Admin configuration for Film
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


# Admin configuration for Show
@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('film', 'location', 'eventtime', 'created_by', 'created_on')
    list_filter = ('eventtime', 'location', 'film')
    search_fields = ('film__name', 'location__name', 'created_by__username')
    ordering = ('eventtime',)


# Admin configuration for Comment
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'show', 'created_on')
    list_filter = ('created_on',)
    search_fields = ('author__username', 'show__title')
    ordering = ('-created_on',)


# Admin configuration for Location
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
