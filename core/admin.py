from django.contrib import admin
from .models import Painting_detail


class PaintingDetailAdmin(admin.ModelAdmin):
    list_display = ('p_title', 'p_artist', 'p_price', 'p_image_url')

admin.site.register(Painting_detail, PaintingDetailAdmin)


