from django.contrib import admin
from .models import Party, Candidate, CandidateRegion

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'color']
    search_fields = ['name', 'abbreviation']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'party', 'position', 'is_active']
    list_filter = ['position', 'party', 'is_active']
    search_fields = ['name']

@admin.register(CandidateRegion)
class CandidateRegionAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'region', 'influence_score', 'support_percentage']
    list_filter = ['region']
    search_fields = ['candidate__name', 'region__name']
