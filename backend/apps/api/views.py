from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Sum, Count
from django.db.models import Q 
from django.utils import timezone

from datetime import timedelta
from apps.regions.models import Region
from apps.candidates.models import Candidate, CandidateRegion, Party
from apps.news.models import NewsArticle
from .serializers import (
    RegionSerializer, CandidateSerializer,
    CandidateRegionSerializer, NewsArticleSerializer, PartySerializer
)

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    
    @action(detail=True, methods=['get'])
    def candidates(self, request, pk=None):
        region = self.get_object()
        influences = CandidateRegion.objects.filter(region=region).select_related('candidate', 'candidate__party')
        serializer = CandidateRegionSerializer(influences, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        region = self.get_object()
        influences = CandidateRegion.objects.filter(region=region)
        
        return Response({
            'id': region.id,
            'name': region.name,
            'population': region.population,
            'total_candidates': influences.count(),
            'avg_influence': influences.aggregate(Avg('influence_score'))['influence_score__avg'] or 0,
            'avg_sentiment': influences.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0,
            'top_candidate': influences.order_by('-influence_score').first().candidate.name if influences.exists() else None
        })
        
    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """
        Returns the full hierarchy for a county:
        county -> constituencies -> wards
        """
        region = self.get_object()

        def build(reg):
            children = Region.objects.filter(parent=reg).order_by('name')
            return {
                'id': reg.id,
                'name': reg.name,
                'code': reg.code,
                'type': reg.region_type,
                'children': [build(c) for c in children],
            }

        return Response(build(region))

class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.filter(is_active=True)
    serializer_class = CandidateSerializer
    
    @action(detail=True, methods=['get'])
    def regions(self, request, pk=None):
        candidate = self.get_object()
        influences = CandidateRegion.objects.filter(candidate=candidate).select_related('region')
        
        data = [{
            'region': inf.region.name,
            'region_id': inf.region.id,
            'influence': inf.influence_score,
            'sentiment': inf.sentiment_score,
            'support': inf.support_percentage,
            'mentions': inf.news_mentions + inf.social_mentions
        } for inf in influences]
        
        return Response(data)

class InfluenceViewSet(viewsets.ModelViewSet):
    queryset = CandidateRegion.objects.all()
    serializer_class = CandidateRegionSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        total_candidates = Candidate.objects.filter(is_active=True).count()
        total_regions = Region.objects.count()
        total_mentions = CandidateRegion.objects.aggregate(
            total=Sum('news_mentions') + Sum('social_mentions')
        )['total'] or 0
        
        avg_influence = CandidateRegion.objects.aggregate(Avg('influence_score'))['influence_score__avg'] or 0
        
        top_candidates = []
        for candidate in Candidate.objects.filter(is_active=True):
            influences = CandidateRegion.objects.filter(candidate=candidate)
            avg_inf = influences.aggregate(Avg('influence_score'))['influence_score__avg'] or 0
            avg_sent = influences.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0
            top_candidates.append({
                'id': candidate.id,
                'name': candidate.name,
                'party': candidate.party.name,
                'party_color': candidate.party.color,
                'average_influence': avg_inf,
                'average_sentiment': avg_sent,
                'regions': influences.count()
            })
        
        top_candidates.sort(key=lambda x: x['average_influence'], reverse=True)
        
        return Response({
            'total_candidates': total_candidates,
            'total_regions': total_regions,
            'total_mentions': total_mentions,
            'average_influence': avg_influence,
            'top_candidates': top_candidates[:5]
        })
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        days = int(request.query_params.get('days', 30))
        data = []
        for i in range(days, 0, -1):
            date = timezone.now() - timedelta(days=i)
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'influence': 50 + (i * 0.5) + (i % 5 - 2) * 3,
                'sentiment': 0.3 + (i * 0.01) + (i % 3 - 1) * 0.1
            })
        return Response(data)

class NewsViewSet(viewsets.ModelViewSet):
    queryset = NewsArticle.objects.all().order_by('-published_date')
    serializer_class = NewsArticleSerializer
    

    def get_queryset(self):
        qs = super().get_queryset()

        region = self.request.query_params.get('region')
        if region:
            qs = qs.filter(regions_mentioned__id=region)

        candidate = self.request.query_params.get('candidate')
        if candidate:
            qs = qs.filter(candidates_mentioned__id=candidate)

        sentiment = self.request.query_params.get('sentiment')
        if sentiment in ('positive', 'negative', 'neutral'):
            qs = qs.filter(sentiment_label=sentiment)

        source = self.request.query_params.get('source')
        if source:
            qs = qs.filter(source__iexact=source)

        search = self.request.query_params.get('q')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        return qs.distinct()

    @action(detail=False, methods=['get'])
    def latest(self, request):
        limit = int(request.query_params.get('limit', 10))
        news = self.get_queryset()[:limit]
        serializer = self.get_serializer(news, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_region(self, request):
        """Return counts of articles per region — useful for a heatmap."""
        rows = (
            NewsArticle.objects
            .values('regions_mentioned__name', 'regions_mentioned__id')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response([
            {
                'region': r['regions_mentioned__name'],
                'region_id': r['regions_mentioned__id'],
                'count': r['count'],
            }
            for r in rows if r['regions_mentioned__name']
        ])

class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer

class DashboardViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def overview(self, request):
        total_candidates = Candidate.objects.filter(is_active=True).count()
        total_regions = Region.objects.count()
        total_news = NewsArticle.objects.count()
        
        influences = CandidateRegion.objects.all()
        avg_influence = influences.aggregate(Avg('influence_score'))['influence_score__avg'] or 0
        
        recent_news = NewsArticle.objects.all()[:5]
        
        return Response({
            'stats': {
                'total_candidates': total_candidates,
                'total_regions': total_regions,
                'total_news': total_news,
                'avg_influence': avg_influence
            },
            'recent_news': NewsArticleSerializer(recent_news, many=True).data
        })
        

class AnalyticsViewSet(viewsets.ViewSet):
    """
    Aggregated endpoints for the Analytics page.
    """

    def _parse_days(self, request):
        try:
            return max(1, min(365, int(request.query_params.get('days', 30))))
        except (TypeError, ValueError):
            return 30

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Overall stats for the header cards."""
        days = self._parse_days(request)
        cutoff = timezone.now() - timedelta(days=days)

        qs = NewsArticle.objects.filter(published_date__gte=cutoff)
        total = qs.count()

        if total == 0:
            return Response({
                'total_articles': 0,
                'positive_pct': 0,
                'negative_pct': 0,
                'neutral_pct': 0,
                'avg_sentiment': 0,
                'days': days,
            })

        positive = qs.filter(sentiment_label='positive').count()
        negative = qs.filter(sentiment_label='negative').count()
        neutral = qs.filter(sentiment_label='neutral').count()
        avg = qs.aggregate(a=Avg('sentiment_score'))['a'] or 0

        return Response({
            'total_articles': total,
            'positive_pct': round(positive / total * 100, 1),
            'negative_pct': round(negative / total * 100, 1),
            'neutral_pct': round(neutral / total * 100, 1),
            'avg_sentiment': round(avg, 3),
            'days': days,
        })

    @action(detail=False, methods=['get'])
    def sentiment_timeline(self, request):
        """Daily average sentiment for the line chart."""
        days = self._parse_days(request)
        cutoff = timezone.now() - timedelta(days=days)

        rows = (
            NewsArticle.objects
            .filter(published_date__gte=cutoff)
            .annotate(date=TruncDate('published_date'))
            .values('date')
            .annotate(
                avg_sentiment=Avg('sentiment_score'),
                count=Count('id'),
            )
            .order_by('date')
        )

        return Response([
            {
                'date': r['date'].strftime('%Y-%m-%d'),
                'sentiment': round(r['avg_sentiment'] or 0, 3),
                'count': r['count'],
            }
            for r in rows
        ])

    @action(detail=False, methods=['get'])
    def coverage_by_region(self, request):
        """Article count per county."""
        days = self._parse_days(request)
        cutoff = timezone.now() - timedelta(days=days)

        rows = (
            Region.objects
            .filter(region_type='county')
            .annotate(
                article_count=Count(
                    'news_articles',
                    filter=Q(news_articles__published_date__gte=cutoff),
                )
            )
            .filter(article_count__gt=0)
            .values('id', 'name', 'article_count')
            .order_by('-article_count')
        )

        return Response(list(rows))

    @action(detail=False, methods=['get'])
    def candidate_coverage(self, request):
        """Mention count per candidate, plus sentiment."""
        days = self._parse_days(request)
        cutoff = timezone.now() - timedelta(days=days)

        rows = (
            Candidate.objects
            .filter(is_active=True)
            .annotate(
                mention_count=Count(
                    'news_articles',
                    filter=Q(news_articles__published_date__gte=cutoff),
                ),
                avg_sentiment=Avg(
                    'news_articles__sentiment_score',
                    filter=Q(news_articles__published_date__gte=cutoff),
                ),
            )
            .values(
                'id', 'name',
                'party__name', 'party__color',
                'mention_count', 'avg_sentiment',
            )
            .order_by('-mention_count')
        )

        return Response([
            {
                'id': r['id'],
                'name': r['name'],
                'party': r['party__name'],
                'party_color': r['party__color'],
                'mentions': r['mention_count'],
                'avg_sentiment': round(r['avg_sentiment'] or 0, 3),
            }
            for r in rows
        ])

    @action(detail=False, methods=['get'])
    def source_breakdown(self, request):
        """Article count per source."""
        days = self._parse_days(request)
        cutoff = timezone.now() - timedelta(days=days)

        rows = (
            NewsArticle.objects
            .filter(published_date__gte=cutoff)
            .values('source')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response(list(rows))

    @action(detail=False, methods=['get'])
    def sentiment_distribution(self, request):
        """Positive / neutral / negative counts."""
        days = self._parse_days(request)
        cutoff = timezone.now() - timedelta(days=days)

        qs = NewsArticle.objects.filter(published_date__gte=cutoff)
        return Response({
            'positive': qs.filter(sentiment_label='positive').count(),
            'neutral': qs.filter(sentiment_label='neutral').count(),
            'negative': qs.filter(sentiment_label='negative').count(),
        })

    @action(detail=False, methods=['get'])
    def latest_articles(self, request):
        """Most recent N articles with full data."""
        limit = min(int(request.query_params.get('limit', 15)), 50)
        qs = (
            NewsArticle.objects
            .prefetch_related('candidates_mentioned', 'regions_mentioned')
            .order_by('-published_date')[:limit]
        )

        return Response([
            {
                'id': a.id,
                'title': a.title,
                'source': a.source,
                'url': a.url,
                'published_date': a.published_date,
                'sentiment_score': a.sentiment_score,
                'sentiment_label': a.sentiment_label,
                'image_url': a.image_url,
                'candidates': [
                    {'id': c.id, 'name': c.name} for c in a.candidates_mentioned.all()
                ],
                'regions': [
                    {'id': r.id, 'name': r.name} for r in a.regions_mentioned.all()
                ],
            }
            for a in qs
        ])