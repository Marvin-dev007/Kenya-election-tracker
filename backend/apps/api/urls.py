from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegionViewSet, CandidateViewSet, InfluenceViewSet,
    NewsViewSet, PartyViewSet, DashboardViewSet
)
from .views import AnalyticsViewSet

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='regions')
router.register(r'candidates', CandidateViewSet, basename='candidates')
router.register(r'influences', InfluenceViewSet, basename='influences')
router.register(r'news', NewsViewSet, basename='news')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'parties', PartyViewSet, basename='parties')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
