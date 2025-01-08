from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from blog.models import Film, Comment, Show, Location, SiteUser
from django.utils.timezone import now

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


# Admin configuration for show
@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('film', 'location', 'eventtime', 'credits', 'status')
    list_filter = ('status', 'location', 'eventtime')
    actions = ['mark_confirmed', 'mark_cancelled', 'mark_completed']

    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, "Selected shows have been marked as confirmed.")

    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, "Selected shows have been marked as cancelled.")

    def mark_completed(self, request, queryset):
        for show in queryset:
            if show.eventtime < now():
                show.status = 'completed'
                show.save()
            else:
                self.message_user(request, f"Show '{show}' cannot be marked as completed because it hasn't occurred yet.", level='error')

    mark_confirmed.short_description = "Mark selected shows as confirmed"
    mark_cancelled.short_description = "Mark selected shows as cancelled"
    mark_completed.short_description = "Mark selected shows as completed"


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
