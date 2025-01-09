from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from blog.models import Film, Comment, Show, Location, SiteUser, ShowCreditLog
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

    def get_readonly_fields(self, request, obj=None):
        """Ensure 'credits' is editable only by superusers."""
        readonly_fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields += ('credits',)
        return readonly_fields


# Admin configuration for Film
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


# Admin configuration for ShowCreditLog
@admin.register(ShowCreditLog)
class ShowCreditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'show', 'credits')
    list_filter = ('show', 'user')
    search_fields = ('user__username', 'show__film__name')
    ordering = ('-id',)


# Admin configuration for Show
@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('film', 'location', 'eventtime', 'credits', 'status')
    list_filter = ('status', 'location', 'eventtime')
    actions = ['mark_confirmed', 'mark_cancelled', 'mark_completed', 'refund_credits']

    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, "Selected shows have been marked as confirmed.")

    def mark_cancelled(self, request, queryset):
        for show in queryset:
            show.cancel_show()
        self.message_user(request, "Selected shows have been marked as cancelled and credits refunded.")

    def mark_completed(self, request, queryset):
        for show in queryset:
            if show.eventtime < now():
                show.mark_completed()
                self.message_user(request, f"Show '{show}' has been marked as completed.")
            else:
                self.message_user(request, f"Show '{show}' cannot be marked as completed because it hasn't occurred yet.", level='error')

    def refund_credits(self, request, queryset):
        for show in queryset:
            show.refund_credits()
        self.message_user(request, "Credits have been refunded for selected shows.")

    mark_confirmed.short_description = "Mark selected shows as confirmed"
    mark_cancelled.short_description = "Mark selected shows as cancelled"
    mark_completed.short_description = "Mark selected shows as completed"
    refund_credits.short_description = "Refund credits for selected shows"


# Admin configuration for Comment
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'show', 'created_on')
    list_filter = ('created_on',)
    search_fields = ('author__username', 'show__film__name')
    ordering = ('-created_on',)


# Admin configuration for Location
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_capacity')
    search_fields = ('name',)
    ordering = ('name',)
