"""
Management command: fetch_news

Fetches news articles from RSS feeds, runs sentiment analysis,
and links them to Kenyan regions and candidates mentioned in the text.

Usage:
    python manage.py fetch_news
    python manage.py fetch_news --feed=standard
    python manage.py fetch_news --lookback-days=3
    python manage.py fetch_news --dry-run
    python manage.py fetch_news --reset
"""

import re
import hashlib
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from apps.news.models import NewsArticle
from apps.regions.models import Region
from apps.candidates.models import Candidate


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RSS feeds — Kenyan and international sources covering Kenyan news
# ---------------------------------------------------------------------------

FEEDS = {
    'standard': {
        'url': 'https://www.standardmedia.co.ke/rss/headlines.php',
        'source': 'The Standard',
    },
    'nation': {
        'url': 'https://nation.africa/kenya/rss',
        'source': 'Daily Nation',
    },
    'citizen': {
        'url': 'https://www.citizen.digital/rss',
        'source': 'Citizen Digital',
    },
    'ktn': {
        'url': 'https://www.standardmedia.co.ke/rss/ktn.php',
        'source': 'KTN News',
    },
    'the-star': {
        'url': 'https://www.the-star.co.ke/rss',
        'source': 'The Star Kenya',
    },
    'bbc-africa': {
        'url': 'https://feeds.bbci.co.uk/news/world/africa/rss.xml',
        'source': 'BBC Africa',
    },
    'capital-news': {
        'url': 'https://www.capitalfm.co.ke/news/feed/',
        'source': 'Capital News',
    },
}


# ---------------------------------------------------------------------------
# Keyword matching
# ---------------------------------------------------------------------------

# County aliases: how the county might be mentioned in text
COUNTY_ALIASES = {
    'nairobi': ['nairobi', 'nairobi county', 'capital'],
    'kisumu': ['kisumu'],
    'mombasa': ['mombasa'],
    'nakuru': ['nakuru'],
    'uasin gishu': ['uasin gishu', 'eldoret'],
    'kiambu': ['kiambu'],
    'kilifi': ['kilifi', 'malindi', 'watamu'],
    'garissa': ['garissa'],
    'kakamega': ['kakamega'],
    'meru': ['meru'],
    'turkana': ['turkana', 'lodwar'],
    'machakos': ['machakos'],
}

# Candidate aliases: full names + common short forms
CANDIDATE_ALIASES = {
    'William Ruto': ['william ruto', 'ruto', 'william samoei ruto'],
    'Raila Odinga': ['raila odinga', 'raila', 'odinga', 'baba'],
    'Uhuru Kenyatta': ['uhuru kenyatta', 'uhuru', 'kenyatta'],
    'Kalombo Musyoka': ['kalombo musyoka', 'kalombo', 'musyoka'],
}

# Sensitive topics that might skew sentiment — flag but don't filter
VIOLENCE_KEYWORDS = [
    'violence', 'clashes', 'protest', 'riot', 'kill', 'death',
    'stab', 'shoot', 'police brutality',
]


class Command(BaseCommand):
    help = 'Fetch and analyze news articles from Kenyan RSS feeds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--feed',
            type=str,
            help='Fetch only one feed (by key). See FEEDS dict for keys.',
        )
        parser.add_argument(
            '--lookback-days',
            type=int,
            default=None,
            help='Ignore articles older than N days (default from settings)',
        )
        parser.add_argument(
            '--max-per-feed',
            type=int,
            default=None,
            help='Max articles per feed (default from settings)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and analyze but do not save',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete ALL existing news articles first',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print per-article diagnostics',
        )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.dry_run = options['dry_run']

        lookback = options['lookback_days'] or getattr(
            settings, 'NEWS_FETCH_LOOKBACK_DAYS', 7
        )
        max_per_feed = options['max_per_feed'] or getattr(
            settings, 'NEWS_FETCH_MAX_PER_FEED', 30
        )
        self.cutoff = timezone.now() - timedelta(days=lookback)

        if options['reset'] and not self.dry_run:
            count = NewsArticle.objects.count()
            NewsArticle.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'🗑  Deleted {count} existing articles'
            ))

        # Load reference data once
        self.analyzer = SentimentIntensityAnalyzer()
        self.regions = list(Region.objects.filter(region_type='county'))
        self.candidates = list(Candidate.objects.filter(is_active=True))

        if not self.regions:
            self.stdout.write(self.style.ERROR(
                '❌ No county regions in database. Run `python manage.py seed_kenya` first.'
            ))
            return

        if not self.candidates:
            self.stdout.write(self.style.WARNING(
                '⚠️  No candidates found — articles will not be linked to candidates'
            ))

        # Select feeds to process
        if options['feed']:
            key = options['feed'].lower()
            if key not in FEEDS:
                raise ValueError(
                    f'Unknown feed "{key}". Valid keys: {", ".join(FEEDS)}'
                )
            feeds = {key: FEEDS[key]}
        else:
            feeds = FEEDS

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'📰 Fetching news from {len(feeds)} feed(s)'
        ))

        total_created = 0
        total_skipped = 0
        total_failed = 0

        for key, feed_meta in feeds.items():
            try:
                created, skipped, failed = self._process_feed(
                    key, feed_meta, max_per_feed
                )
                total_created += created
                total_skipped += skipped
                total_failed += failed
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'❌ Feed {key} failed: {e}'
                ))
                logger.exception(f'Feed {key} failed')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('📊 Summary'))
        self.stdout.write(f'   Created:  {total_created}')
        self.stdout.write(f'   Skipped:  {total_skipped} (already in DB or too old)')
        self.stdout.write(f'   Failed:   {total_failed}')
        self.stdout.write(f'   Total in DB: {NewsArticle.objects.count()}')

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '🧪 Dry run — nothing was saved'
            ))

    # ------------------------------------------------------------------
    # Feed processing
    # ------------------------------------------------------------------

    def _process_feed(self, key, feed_meta, max_entries):
        self.stdout.write(f'\n→ {feed_meta["source"]}')
        self.stdout.write(f'   {feed_meta["url"]}')

        parsed = feedparser.parse(feed_meta['url'])

        if parsed.bozo:
            self.stdout.write(self.style.WARNING(
                f'   ⚠️  Feed parsing issue: {parsed.bozo_exception}'
            ))

        entries = parsed.entries[:max_entries]
        self.stdout.write(f'   {len(entries)} entries found')

        created = skipped = failed = 0

        for entry in entries:
            try:
                result = self._process_entry(entry, feed_meta['source'])
                if result == 'created':
                    created += 1
                elif result == 'skipped':
                    skipped += 1
            except Exception as e:
                failed += 1
                logger.warning(f'Entry failed: {e}')
                if self.verbose:
                    self.stdout.write(self.style.ERROR(
                        f'   ❌ {entry.get("title", "?")[:60]}: {e}'
                    ))

        self.stdout.write(
            f'   ✅ Created: {created} | Skipped: {skipped} | Failed: {failed}'
        )
        return created, skipped, failed

    def _process_entry(self, entry, source_name):
        title = (entry.get('title') or '').strip()
        url = (entry.get('link') or '').strip()

        if not title or not url:
            return 'skipped'

        if len(title) < getattr(settings, 'NEWS_FETCH_MIN_TITLE_LENGTH', 20):
            return 'skipped'

        # Normalize URL (strip tracking params)
        url = self._normalize_url(url)

        # Skip if already in DB
        if NewsArticle.objects.filter(url=url).exists():
            return 'skipped'

        # Parse published date
        published_date = self._parse_date(entry)

        # Skip if too old
        if published_date and published_date < self.cutoff:
            if self.verbose:
                self.stdout.write(f'   ⏭  Too old: {title[:50]}')
            return 'skipped'

        # Extract content
        summary_html = entry.get('summary') or entry.get('description') or ''
        content_html = ''
        if entry.get('content'):
            content_html = entry['content'][0].get('value', '')

        full_text = self._html_to_text(content_html or summary_html)
        summary = self._html_to_text(summary_html)[:500]

        if not full_text:
            return 'skipped'

        # Sentiment analysis
        sentiment = self._analyze_sentiment(title + ' ' + full_text)

        # Extract mentions
        mentioned_regions = self._extract_regions(title + ' ' + full_text)
        mentioned_candidates = self._extract_candidates(title + ' ' + full_text)

        # Image URL (if present)
        image_url = self._extract_image(entry)

        # Create the article (unless dry-run)
        if self.dry_run:
            if self.verbose:
                self.stdout.write(
                    f'   🧪 Would create: {title[:60]} '
                    f'[sent={sentiment["score"]:.2f}, '
                    f'regions={len(mentioned_regions)}, '
                    f'candidates={len(mentioned_candidates)}]'
                )
            return 'created'

        with transaction.atomic():
            article = NewsArticle.objects.create(
                title=title[:500],
                content=full_text,
                summary=summary,
                source=source_name,
                url=url,
                published_date=published_date or timezone.now(),
                sentiment_score=sentiment['score'],
                sentiment_label=sentiment['label'],
                engagement_count=0,
                image_url=image_url or '',
                is_verified=self._is_verified_source(source_name),
            )
            if mentioned_regions:
                article.regions_mentioned.set(mentioned_regions)
            if mentioned_candidates:
                article.candidates_mentioned.set(mentioned_candidates)

        if self.verbose:
            self.stdout.write(
                f'   ✅ {title[:60]} '
                f'[sent={sentiment["score"]:.2f}, '
                f'regions={len(mentioned_regions)}, '
                f'candidates={len(mentioned_candidates)}]'
            )
        return 'created'

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def _html_to_text(self, html):
        if not html:
            return ''
        soup = BeautifulSoup(html, 'lxml')
        # Drop scripts/styles
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        text = soup.get_text(separator=' ')
        return re.sub(r'\s+', ' ', text).strip()

    def _normalize_url(self, url):
        """Strip common tracking query params."""
        try:
            parsed = urlparse(url)
            return f'{parsed.scheme}://{parsed.netloc}{parsed.path}'.rstrip('/')
        except Exception:
            return url

    def _parse_date(self, entry):
        for key in ('published', 'updated', 'created'):
            raw = entry.get(key)
            if not raw:
                continue
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=dt_timezone.utc)
                return dt
            except Exception:
                continue
        return None

    def _extract_image(self, entry):
        # Try media:content, media:thumbnail, enclosure, or first <img> in content
        if entry.get('media_content'):
            return entry['media_content'][0].get('url', '')
        if entry.get('media_thumbnail'):
            return entry['media_thumbnail'][0].get('url', '')
        for link in entry.get('links', []):
            if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
                return link.get('href', '')
        if entry.get('content'):
            html = entry['content'][0].get('value', '')
            soup = BeautifulSoup(html, 'lxml')
            img = soup.find('img')
            if img and img.get('src'):
                return img['src']
        return ''

    # ------------------------------------------------------------------
    # Sentiment
    # ------------------------------------------------------------------

    def _analyze_sentiment(self, text):
        scores = self.analyzer.polarity_scores(text[:5000])  # cap for speed
        compound = scores['compound']

        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'score': round(compound, 3),
            'label': label,
            'pos': round(scores['pos'], 3),
            'neg': round(scores['neg'], 3),
            'neu': round(scores['neu'], 3),
        }

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    def _extract_regions(self, text):
        text_lower = text.lower()
        matched = []

        for region in self.regions:
            name_lower = region.name.lower()
            aliases = COUNTY_ALIASES.get(name_lower, [name_lower])
            if any(self._word_in_text(alias, text_lower) for alias in aliases):
                matched.append(region)

        return matched

    def _extract_candidates(self, text):
        text_lower = text.lower()
        matched = []

        for candidate in self.candidates:
            aliases = CANDIDATE_ALIASES.get(candidate.name, [candidate.name.lower()])
            if any(self._word_in_text(alias, text_lower) for alias in aliases):
                matched.append(candidate)

        return matched

    def _word_in_text(self, word, text):
        """Match word boundaries so 'meru' doesn't match 'mercury'."""
        pattern = r'\b' + re.escape(word) + r'\b'
        return re.search(pattern, text) is not None

    # ------------------------------------------------------------------
    # Source trust
    # ------------------------------------------------------------------

    def _is_verified_source(self, source_name):
        verified = {'Daily Nation', 'The Standard', 'Citizen Digital',
                    'KTN News', 'The Star Kenya', 'BBC Africa', 'Capital News'}
        return source_name in verified