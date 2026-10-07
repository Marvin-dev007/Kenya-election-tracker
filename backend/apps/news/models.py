from django.db import models
from apps.regions.models import Region
from apps.candidates.models import Candidate

class NewsArticle(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField()
    summary = models.TextField(blank=True)
    source = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    published_date = models.DateTimeField()
    fetched_date = models.DateTimeField(auto_now_add=True)
    sentiment_score = models.FloatField(default=0.0)
    sentiment_label = models.CharField(max_length=20, blank=True)
    engagement_count = models.IntegerField(default=0)
    regions_mentioned = models.ManyToManyField(Region, related_name='news_articles')
    candidates_mentioned = models.ManyToManyField(Candidate, related_name='news_articles')
    image_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-published_date']
    
    def __str__(self):
        return self.title[:100]
