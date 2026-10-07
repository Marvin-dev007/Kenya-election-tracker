from rest_framework import serializers
from apps.regions.models import Region
from apps.candidates.models import Party, Candidate, CandidateRegion
from apps.news.models import NewsArticle

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'code', 'region_type', 'parent', 
                 'center_lat', 'center_lng', 'population']

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ['id', 'name', 'abbreviation', 'color', 'logo']

class CandidateSerializer(serializers.ModelSerializer):
    party_detail = PartySerializer(source='party', read_only=True)
    
    class Meta:
        model = Candidate
        fields = ['id', 'name', 'photo', 'party', 'party_detail', 
                 'position', 'biography', 'age', 'is_active']

class CandidateRegionSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    candidate_party = serializers.CharField(source='candidate.party.name', read_only=True)
    party_color = serializers.CharField(source='candidate.party.color', read_only=True)
    
    class Meta:
        model = CandidateRegion
        fields = ['id', 'candidate', 'candidate_name', 'candidate_party', 'party_color',
                 'region', 'region_name', 'influence_score', 'sentiment_score',
                 'support_percentage', 'news_mentions', 'social_mentions',
                 'positive_mentions', 'negative_mentions', 'neutral_mentions',
                 'last_updated']

class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = ['id', 'title', 'summary', 'source', 'published_date', 
                 'sentiment_score', 'sentiment_label', 'image_url', 'url']
