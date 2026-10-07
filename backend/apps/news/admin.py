from django.contrib import admin
from .models import NewsArticle

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'published_date', 'sentiment_score']
    list_filter = ['source', 'is_verified']
    search_fields = ['title', 'content']
