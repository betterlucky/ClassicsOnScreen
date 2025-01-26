from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from blog.models import Film, Comment, Show, Location, SiteUser, ShowCreditLog
from django.utils.timezone import now
from django.core.mail import send_mail
from django.db.models import Sum
from django.conf import settings
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import render
from django.http import JsonResponse
import requests


# Inline configuration for shows created by a user
class ShowInline(admin.TabularInline):
    model = Show
    extra = 0
    fields = ('film', 'location', 'eventtime', 'created_on')
    readonly_fields = ('created_on',)


@admin.register(ShowCreditLog)
class ShowCreditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'show', 'credits', 'view_log_link')
    list_filter = ('show', 'user')
    search_fields = ('user__username', 'show__film__name')
    ordering = ('-id',)

    def view_log_link(self, obj):
        # Generate a link to the custom view_log page for the show
        url = f"/admin/{obj._meta.app_label}/{obj._meta.model_name}/view_log/{obj.show.id}/"
        return format_html('<a href="{}">View Log</a>', url)

    view_log_link.short_description = 'View Log'

    def get_urls(self):
        # Add a custom URL for viewing the log of a specific show
        urls = super().get_urls()
        custom_urls = [
            path('view_log/<int:show_id>/', self.admin_site.admin_view(self.view_log), name='view_log'),
        ]
        return custom_urls + urls

    def view_log(self, request, show_id):
        # Get all ShowCreditLog entries for a specific show
        show = Show.objects.get(id=show_id)
        log_entries = ShowCreditLog.objects.filter(show=show).order_by('-id')

        context = {
            'title': f"Credit Log for {show.film}",
            'log_entries': log_entries,
            'show': show,
        }
        context['back_to_show_credits_url'] = '/admin/blog/showcreditlog/'
        return render(request, 'admin/view_show_credit_log.html', context)


# Admin configuration for Film
@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'imdb_code', 'description')
    list_filter = ('active',)
    search_fields = ('name', 'imdb_code')
    ordering = ('name',)
    list_editable = ('active',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'imdb_code', 'description')
        }),
        ('Status', {
            'fields': ('active',),
            'description': 'Active films will be shown in the available films count'
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['imdb_code'].required = True
        return form

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('imdb-search/', self.admin_site.admin_view(self.imdb_search), name='imdb-search'),
        ]
        return custom_urls + urls

    def imdb_search(self, request):
        if 'term' in request.GET:
            try:
                response = requests.get(
                    'http://www.omdbapi.com/',
                    params={
                        's': request.GET['term'],
                        'apikey': settings.OMDB_API_KEY,
                        'type': 'movie'
                    }
                )
                data = response.json()
                if data.get('Response') == 'True':
                    results = [
                        {
                            'id': movie['imdbID'],
                            'text': f"{movie['Title']} ({movie['Year']})",
                            'title': movie['Title']
                        }
                        for movie in data.get('Search', [])
                    ]
                    return JsonResponse({'results': results})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'results': []})

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',)
        }
        js = (
            'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
            'admin/js/imdb-search.js',
        )


# Admin configuration for Show
@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('film', 'location', 'eventtime', 'credits', 'status')
    list_filter = ('status', 'location', 'eventtime')
    actions = ['mark_confirmed', 'mark_cancelled', 'mark_completed', 'refund_credits', 'email_guest_lists']

    def mark_confirmed(self, request, queryset):
        for show in queryset:
            show.confirm_show()
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

    def email_guest_lists(self, request, queryset):
        """Email the guest list for selected shows."""
        for show in queryset:
            # Generate the guest list
            guest_list = (
                show.credit_logs.values(
                    'user__username', 'user__email', 'user__first_name', 'user__last_name'
                )
                .annotate(total_credits=Sum('credits'))
                .order_by('-total_credits')
            )

            # Create email content
            guest_list_text = f"Guest List for Show: {show.film.name} at {show.location.name} on {show.eventtime}\n\n"
            guest_list_text += "Username | First Name | Last Name | Email | Tickets\n"
            guest_list_text += "-" * 60 + "\n"

            for guest in guest_list:
                guest_list_text += (
                    f"{guest['user__username']} | "
                    f"{guest['user__first_name']} | "
                    f"{guest['user__last_name']} | "
                    f"{guest['user__email']} | "
                    f"{guest['total_credits']}\n"
                )

            # Email details
            subject = f"Guest List for {show.film.name}"
            recipient = "classicsbackonscreen@gmail.com"

            try:
                send_mail(
                    subject=subject,
                    message=guest_list_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                )
                self.message_user(request, f"Guest list for '{show}' emailed successfully.")
            except Exception as e:
                self.message_user(request, f"Failed to send guest list for '{show}': {e}", level='error')

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
