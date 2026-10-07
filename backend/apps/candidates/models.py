from django.db import models
from apps.regions.models import Region

class Party(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10, unique=True)
    color = models.CharField(max_length=7, default='#000000')
    logo = models.ImageField(upload_to='parties/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Candidate(models.Model):
    POSITIONS = [
        ('president', 'President'),
        ('governor', 'Governor'),
        ('senator', 'Senator'),
        ('mp', 'Member of Parliament'),
        ('mca', 'Member of County Assembly'),
    ]
    
    name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='candidates/', null=True, blank=True)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='candidates')
    position = models.CharField(max_length=20, choices=POSITIONS)
    biography = models.TextField(blank=True)
    manifesto = models.TextField(blank=True)
    age = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_position_display()}"
    
    class Meta:
        ordering = ['name']

class CandidateRegion(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='region_influences')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='candidate_influences')
    influence_score = models.FloatField(default=0.0)
    sentiment_score = models.FloatField(default=0.0)
    support_percentage = models.FloatField(default=0.0)
    news_mentions = models.IntegerField(default=0)
    social_mentions = models.IntegerField(default=0)
    positive_mentions = models.IntegerField(default=0)
    negative_mentions = models.IntegerField(default=0)
    neutral_mentions = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['candidate', 'region']
        ordering = ['-influence_score']
    
    def __str__(self):
        return f"{self.candidate.name} in {self.region.name}"
