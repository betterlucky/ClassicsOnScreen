from django.contrib import admin

from blog.models import Film, Comment, Show, Location


class FilmAdmin(admin.ModelAdmin):
    pass


class ShowAdmin(admin.ModelAdmin):
    pass


class CommentAdmin(admin.ModelAdmin):
    pass


class LocationAdmin(admin.ModelAdmin):
    pass

admin.site.register(Film, FilmAdmin)
admin.site.register(Show, ShowAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Location, LocationAdmin)

