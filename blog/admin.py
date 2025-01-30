from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from blog.models import Film, Comment, Show, Location, SiteUser, ShowCreditLog, VenueOwner, ShowOption, FAQ
from django.utils.timezone import now
from django.core.mail import send_mail
from django.db.models import Sum
from django.conf import settings
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
import requests
import csv
from io import StringIO
from django.contrib import messages


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
    list_display = ('name', 'active', 'imdb_code', 'EDI_number')
    list_filter = ('active',)
    search_fields = ('name', 'imdb_code', 'EDI_number')
    ordering = ('name',)
    list_editable = ('active',)
    actions = ['deactivate_films', 'export_active_films']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'imdb_code', 'EDI_number')
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

    def deactivate_films(self, request, queryset):
        """Admin action to deactivate selected films"""
        success_films = []
        error_messages = []

        # Process all films
        for film in queryset:
            if film.has_active_shows():
                error_messages.append(f"Cannot remove '{film.name}' - has active shows")
                continue

            # Cancel all votes
            film.votes.all().delete()
            
            # Deactivate film
            film.active = False
            film.save()

            success_films.append(film)

        # Send consolidated email if any films were deactivated
        if success_films:
            subject = f"Films Removed: {len(success_films)} films deactivated"
            
            # Create CSV in memory
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Film', 'EDI', 'IMDB'])  # Header row
            
            for film in success_films:
                writer.writerow([
                    film.name,
                    film.EDI_number or 'N/A',
                    film.imdb_code
                ])
            
            # Prepare email message
            message_parts = []
            if error_messages:
                message_parts.append("The following errors occurred:")
                message_parts.extend(error_messages)
                message_parts.append("\n")
            
            message_parts.append(output.getvalue())
            message = "\n".join(message_parts)

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )

        # Show admin messages
        if success_films:
            self.message_user(
                request,
                f"Successfully removed {len(success_films)} film(s)",
                messages.SUCCESS
            )
        
        for error in error_messages:
            self.message_user(request, error, messages.ERROR)

    def export_active_films(self, request, queryset=None):
        """Admin action to export all active films"""
        # Get all active films, ignoring the queryset
        active_films = Film.objects.filter(active=True).order_by('name')
        
        if not active_films.exists():
            self.message_user(request, "No active films found to export", messages.WARNING)
            return

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Film', 'EDI', 'IMDB'])  # Header row
        
        for film in active_films:
            writer.writerow([
                film.name,
                film.EDI_number or 'N/A',
                film.imdb_code
            ])
        
        # Send email
        subject = f"Active Films Export: {active_films.count()} films"
        message = output.getvalue()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )

        self.message_user(
            request,
            f"Exported {active_films.count()} active films to {settings.ADMIN_EMAIL}",
            messages.SUCCESS
        )

    def changelist_view(self, request, extra_context=None):
        """Add export button to changelist view"""
        if 'action' in request.POST and request.POST['action'] == 'export_active_films':
            if not request.POST.getlist('_selected_action'):
                # No films selected, still perform export
                self.export_active_films(request)
                return HttpResponseRedirect(request.get_full_path())
        return super().changelist_view(request, extra_context)

    export_active_films.short_description = "Export active films list"

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
    actions = ['mark_confirmed', 'mark_cancelled', 'mark_completed', 'refund_credits', 'email_guest_lists', 'mark_expired']

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

    def mark_expired(self, request, queryset):
        """Mark selected shows as expired if applicable."""
        for show in queryset:
            if show.status in ['tbc', 'inactive']: #and show.eventtime <= now():
                show.mark_expired()
                self.message_user(request, f"Show '{show}' has been marked as expired.")
            else:
                self.message_user(request, f"Show '{show}' cannot be marked as expired because it is not in 'tbc' or 'inactive' status, or it has not passed its event time.", level='error')

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


# Admin configuration for VenueOwner
@admin.register(VenueOwner)
class VenueOwnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'website')
    search_fields = ('name', 'description', 'contact_email')
    list_filter = ('locations__active',)


# Admin configuration for Location
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'contact_email', 'min_capacity', 'max_capacity', 'active')
    list_filter = ('active', 'owner')
    search_fields = ('name', 'owner__name', 'contact_email')
    readonly_fields = ('get_contact_emails',)

    def get_contact_emails(self, obj):
        emails = obj.get_contact_emails()
        return "\n".join(emails)
    get_contact_emails.short_description = "All Contact Emails"


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


@admin.register(ShowOption)
class ShowOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'description')
    list_filter = ('active',)
    search_fields = ('name', 'description')
    list_editable = ('active',)
    ordering = ('name',)

    def get_queryset(self, request):
        """Show all options to admins."""
        return super().get_queryset(request)

    def has_delete_permission(self, request, obj=None):
        """Only allow deletion if option isn't used by any shows."""
        if obj and obj.shows.exists():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'active')
    list_filter = ('category', 'active')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'active')
    ordering = ('category', 'order', 'created_on')
