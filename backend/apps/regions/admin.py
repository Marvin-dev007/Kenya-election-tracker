from django.contrib import admin
from .models import Region

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'region_type', 'population']
    search_fields = ['name', 'code']
    list_filter = ['region_type']
