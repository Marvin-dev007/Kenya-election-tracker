"""
Management command: seed_kenya

Populates the database with sample election data:
  - 1 superuser (admin / admin123)
  - 4 political parties
  - 10 counties (or --counties=N)
  - Constituencies and wards for each county
  - 4 presidential candidates
  - CandidateRegion influence rows at every level
  - 20 sample news articles

Usage:
    python manage.py seed_kenya
    python manage.py seed_kenya --reset
    python manage.py seed_kenya --counties=5
    python manage.py seed_kenya --no-news
    python manage.py seed_kenya --real-data
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.regions.models import Region
from apps.candidates.models import Party, Candidate, CandidateRegion
from apps.news.models import NewsArticle


# Where the optional JSON boundary files live
DATA_DIR = Path(__file__).resolve().parents[2] / 'data'


# Real Kenyan counties (used when --real-data is passed or JSON is missing)
DEMO_COUNTIES = [
    {'code': 'KE-01', 'name': 'Nairobi',     'lat': -1.286389, 'lng': 36.817223, 'population': 4397073},
    {'code': 'KE-02', 'name': 'Kisumu',      'lat': -0.091702, 'lng': 34.767956, 'population': 1134424},
    {'code': 'KE-03', 'name': 'Mombasa',     'lat': -4.043477, 'lng': 39.668206, 'population': 1208333},
    {'code': 'KE-04', 'name': 'Nakuru',      'lat': -0.303099, 'lng': 36.080026, 'population': 2162202},
    {'code': 'KE-05', 'name': 'Uasin Gishu', 'lat': 0.514278,  'lng': 35.269779, 'population': 1163186},
    {'code': 'KE-06', 'name': 'Kiambu',      'lat': -1.171390, 'lng': 36.835613, 'population': 2417735},
    {'code': 'KE-07', 'name': 'Kilifi',      'lat': -3.630986, 'lng': 39.849918, 'population': 1453787},
    {'code': 'KE-08', 'name': 'Garissa',     'lat': -0.456570, 'lng': 39.658407, 'population': 841353},
    {'code': 'KE-09', 'name': 'Kakamega',    'lat': 0.282731,  'lng': 34.751863, 'population': 1867946},
    {'code': 'KE-10', 'name': 'Meru',        'lat': 0.050000,  'lng': 37.650000, 'population': 1545714},
    {'code': 'KE-11', 'name': 'Turkana',     'lat': 3.116667,  'lng': 35.600000, 'population': 926976},
    {'code': 'KE-12', 'name': 'Machakos',    'lat': -1.517683, 'lng': 37.263409, 'population': 1421932},
]


# Realistic strongholds — used to bias influence scores
CANDIDATE_STRONGHOLDS = {
    'William Ruto':    ['Uasin Gishu', 'Nakuru', 'Kiambu', 'Meru'],
    'Raila Odinga':    ['Nairobi', 'Kisumu', 'Mombasa', 'Kakamega'],
    'Uhuru Kenyatta':  ['Kiambu', 'Nairobi', 'Nakuru'],
    'Kalombo Musyoka': ['Meru', 'Kakamega', 'Kisumu'],
}


PARTIES_DATA = [
    {'name': 'United Democratic Alliance',  'abbr': 'UDA',     'color': '#006600'},
    {'name': 'Orange Democratic Movement',  'abbr': 'ODM',     'color': '#FF6600'},
    {'name': 'Jubilee Party',               'abbr': 'JUBILEE', 'color': '#FF0000'},
    {'name': 'Wiper Democratic Movement',   'abbr': 'WIPER',   'color': '#800080'},
]


CANDIDATES_DATA = [
    {
        'name': 'William Ruto',
        'party': 'UDA',
        'position': 'president',
        'bio': 'Current President of Kenya. Former Deputy President.',
        'age': 57,
    },
    {
        'name': 'Raila Odinga',
        'party': 'ODM',
        'position': 'president',
        'bio': 'Former Prime Minister of Kenya. Veteran opposition leader.',
        'age': 79,
    },
    {
        'name': 'Uhuru Kenyatta',
        'party': 'JUBILEE',
        'position': 'president',
        'bio': 'Former President of Kenya (2013–2022).',
        'age': 62,
    },
    {
        'name': 'Kalombo Musyoka',
        'party': 'WIPER',
        'position': 'president',
        'bio': 'Former Vice President of Kenya.',
        'age': 70,
    },
]


NEWS_SOURCES = ['Daily Nation', 'The Standard', 'Citizen TV', 'KTN News', 'KBC']

NEWS_HEADLINES = [
    'Kenya election campaigns intensify as candidates hit the ground',
    'New opinion poll shows shifting political landscape in key counties',
    'Candidates outline their manifestos for the upcoming election',
    'Youth vote expected to be decisive in Kenya election',
    'Economic issues dominate election campaign in Kenya',
    'Peaceful election urged as Kenya approaches polls',
    'International observers arrive ahead of Kenya election',
    'Digital campaigns play key role in Kenya election',
    'Women leaders call for peaceful elections in Kenya',
    'Religious leaders pray for peaceful election in Kenya',
]


class Command(BaseCommand):
    help = 'Seed the database with Kenya election tracker sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing sample data before seeding',
        )
        parser.add_argument(
            '--counties',
            type=int,
            default=10,
            help='How many counties to seed (default: 10, max: 12)',
        )
        parser.add_argument(
            '--no-news',
            action='store_true',
            help='Skip creating sample news articles',
        )
        parser.add_argument(
            '--real-data',
            action='store_true',
            help='Try to load real boundary JSON from apps/regions/data/',
        )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '🚀 Kenya Election Tracker — Seeding'
        ))
        self.stdout.write('')

        if options['reset']:
            self._reset_data()

        county_count = min(options['counties'], len(DEMO_COUNTIES))
        use_real = options['real_data']

        with transaction.atomic():
            self._create_superuser()
            parties = self._create_parties()
            counties = self._seed_counties(county_count, use_real)
            self._seed_constituencies(counties, use_real)
            self._seed_wards(use_real)
            candidates = self._create_candidates(parties)
            self._seed_candidate_regions(candidates)

            if not options['no_news']:
                self._seed_news(candidates, counties)

        self._print_summary()

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def _reset_data(self):
        self.stdout.write(self.style.WARNING('⚠️  Resetting sample data…'))

        # Order matters: delete children before parents
        CandidateRegion.objects.all().delete()
        NewsArticle.objects.all().delete()
        Candidate.objects.all().delete()
        Party.objects.all().delete()
        Region.objects.all().delete()

        # Keep superuser, but if you want a full wipe, uncomment:
        # User.objects.filter(is_superuser=True).delete()

        self.stdout.write(self.style.SUCCESS('✅ Data reset'))
        self.stdout.write('')

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def _create_superuser(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
            )
            self.stdout.write(self.style.SUCCESS(
                '✅ Superuser: admin / admin123'
            ))
        else:
            self.stdout.write('ℹ️  Superuser already exists')

    # ------------------------------------------------------------------
    # Parties
    # ------------------------------------------------------------------

    def _create_parties(self):
        parties = []
        for p in PARTIES_DATA:
            party, _ = Party.objects.get_or_create(
                abbreviation=p['abbr'],
                defaults={'name': p['name'], 'color': p['color']},
            )
            parties.append(party)
            self.stdout.write(f'✅ Party: {party.name} ({party.abbreviation})')
        return parties

    # ------------------------------------------------------------------
    # Counties
    # ------------------------------------------------------------------

    def _seed_counties(self, limit, use_real):
        """
        Return a list of Region objects that were created or already exist.
        """
        source = self._load_counties_json() if use_real else None
        if not source:
            source = DEMO_COUNTIES[:limit]
        else:
            source = source[:limit]

        counties = []
        for c in source:
            region, created = Region.objects.get_or_create(
                code=c['code'],
                defaults={
                    'name': c['name'],
                    'region_type': 'county',
                    'center_lat': c.get('lat'),
                    'center_lng': c.get('lng'),
                    'population': c.get('population'),
                },
            )
            counties.append(region)
            flag = '✅' if created else 'ℹ️ '
            self.stdout.write(f'{flag} County: {region.name} ({region.code})')

        return counties

    def _load_counties_json(self):
        path = DATA_DIR / 'counties.json'
        if not path.exists():
            self.stdout.write(self.style.WARNING(
                f'⚠️  {path} not found — falling back to built-in data'
            ))
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to read: {e}'))
            return None

        features = data if isinstance(data, list) else data.get('features', [])
        counties = []
        for obj in features:
            props = obj.get('properties', obj)
            code = props.get('county_code') or props.get('code')
            name = props.get('county_name') or props.get('name')
            if not code or not name:
                continue
            counties.append({
                'code': str(code),
                'name': name,
                'lat': props.get('center_lat'),
                'lng': props.get('center_lng'),
                'population': props.get('population'),
            })
        return counties or None

    # ------------------------------------------------------------------
    # Constituencies
    # ------------------------------------------------------------------

    def _seed_constituencies(self, counties, use_real):
        from apps.regions.models import Region as R

        source = self._load_constituencies_json() if use_real else None
        created_count = 0

        if source:
            for c in source:
                parent = next(
                    (county for county in counties
                     if county.code == c.get('parent_code')),
                    None,
                )
                if not parent:
                    continue
                _, created = R.objects.get_or_create(
                    code=c['code'],
                    defaults={
                        'name': c['name'],
                        'region_type': 'constituency',
                        'parent': parent,
                    },
                )
                if created:
                    created_count += 1
        else:
            for county in counties:
                count = random.randint(5, 12)
                for i in range(count):
                    code = f'{county.code}-C{i + 1:02d}'
                    _, created = R.objects.get_or_create(
                        code=code,
                        defaults={
                            'name': f'{county.name} Constituency {i + 1}',
                            'region_type': 'constituency',
                            'parent': county,
                        },
                    )
                    if created:
                        created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Constituencies: {created_count} new'
        ))

    def _load_constituencies_json(self):
        path = DATA_DIR / 'constituencies.json'
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return None

        features = data if isinstance(data, list) else data.get('features', [])
        result = []
        for obj in features:
            props = obj.get('properties', obj)
            code = props.get('constituency_code') or props.get('code')
            name = props.get('constituency_name') or props.get('name')
            parent = props.get('county_code') or props.get('parent_code')
            if code and name and parent:
                result.append({'code': str(code), 'name': name, 'parent_code': str(parent)})
        return result or None

    # ------------------------------------------------------------------
    # Wards
    # ------------------------------------------------------------------

    def _seed_wards(self, use_real):
        from apps.regions.models import Region as R

        source = self._load_wards_json() if use_real else None
        created_count = 0

        if source:
            const_lookup = {
                r.name.lower(): r
                for r in R.objects.filter(region_type='constituency')
            }
            for w in source:
                parent = const_lookup.get(w.get('parent_name', '').lower())
                if not parent:
                    continue
                _, created = R.objects.get_or_create(
                    code=w['code'],
                    defaults={
                        'name': w['name'],
                        'region_type': 'ward',
                        'parent': parent,
                    },
                )
                if created:
                    created_count += 1
        else:
            for constituency in R.objects.filter(region_type='constituency'):
                count = random.randint(5, 8)
                for i in range(count):
                    code = f'{constituency.code}-W{i + 1:02d}'
                    _, created = R.objects.get_or_create(
                        code=code,
                        defaults={
                            'name': f'{constituency.name} Ward {i + 1}',
                            'region_type': 'ward',
                            'parent': constituency,
                        },
                    )
                    if created:
                        created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Wards: {created_count} new'
        ))

    def _load_wards_json(self):
        path = DATA_DIR / 'wards.json'
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return None

        features = data if isinstance(data, list) else data.get('features', [])
        result = []
        for obj in features:
            props = obj.get('properties', obj)
            code = props.get('ward_code') or props.get('code')
            name = props.get('ward_name') or props.get('name')
            parent = props.get('constituency_name') or props.get('parent_name')
            if code and name and parent:
                result.append({'code': str(code), 'name': name, 'parent_name': parent})
        return result or None

    # ------------------------------------------------------------------
    # Candidates
    # ------------------------------------------------------------------

    def _create_candidates(self, parties):
        party_by_abbr = {p.abbreviation: p for p in parties}
        candidates = []

        for cd in CANDIDATES_DATA:
            party = party_by_abbr.get(cd['party'])
            if not party:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  Party {cd["party"]} not found — skipping {cd["name"]}'
                ))
                continue
            candidate, created = Candidate.objects.get_or_create(
                name=cd['name'],
                defaults={
                    'party': party,
                    'position': cd['position'],
                    'biography': cd['bio'],
                    'age': cd['age'],
                    'is_active': True,
                },
            )
            candidates.append(candidate)
            flag = '✅' if created else 'ℹ️ '
            self.stdout.write(f'{flag} Candidate: {candidate.name}')

        return candidates

    # ------------------------------------------------------------------
    # CandidateRegion rows
    # ------------------------------------------------------------------

    def _influence_for(self, candidate_name, region_name):
        strongholds = CANDIDATE_STRONGHOLDS.get(candidate_name, [])
        is_stronghold = any(s.lower() in region_name.lower() for s in strongholds)
        if is_stronghold:
            return random.uniform(65, 92)
        return random.uniform(20, 85)

    def _seed_candidate_regions(self, candidates):
        created = 0

        # County level
        for candidate in candidates:
            for county in Region.objects.filter(region_type='county'):
                influence = self._influence_for(candidate.name, county.name)
                _, was_created = CandidateRegion.objects.get_or_create(
                    candidate=candidate,
                    region=county,
                    defaults={
                        'influence_score': round(influence, 2),
                        'sentiment_score': round(random.uniform(-0.4, 0.8), 2),
                        'support_percentage': round(influence * random.uniform(0.6, 0.95), 2),
                        'news_mentions': random.randint(5, 50),
                        'social_mentions': random.randint(20, 200),
                        'positive_mentions': random.randint(5, 30),
                        'negative_mentions': random.randint(1, 15),
                        'neutral_mentions': random.randint(5, 20),
                    },
                )
                if was_created:
                    created += 1

        # Constituency level
        for candidate in candidates:
            for constituency in Region.objects.filter(region_type='constituency'):
                parent = CandidateRegion.objects.filter(
                    candidate=candidate,
                    region=constituency.parent,
                ).first()
                base = parent.influence_score if parent else 50
                influence = max(0, min(100, base + random.uniform(-15, 15)))
                _, was_created = CandidateRegion.objects.get_or_create(
                    candidate=candidate,
                    region=constituency,
                    defaults={
                        'influence_score': round(influence, 2),
                        'sentiment_score': round(random.uniform(-0.4, 0.8), 2),
                        'support_percentage': round(influence * random.uniform(0.6, 0.95), 2),
                        'news_mentions': random.randint(1, 15),
                        'social_mentions': random.randint(5, 60),
                        'positive_mentions': random.randint(1, 10),
                        'negative_mentions': random.randint(0, 5),
                        'neutral_mentions': random.randint(1, 8),
                    },
                )
                if was_created:
                    created += 1

        # Ward level
        for candidate in candidates:
            for ward in Region.objects.filter(region_type='ward'):
                parent = CandidateRegion.objects.filter(
                    candidate=candidate,
                    region=ward.parent,
                ).first()
                base = parent.influence_score if parent else 50
                influence = max(0, min(100, base + random.uniform(-10, 10)))
                _, was_created = CandidateRegion.objects.get_or_create(
                    candidate=candidate,
                    region=ward,
                    defaults={
                        'influence_score': round(influence, 2),
                        'sentiment_score': round(random.uniform(-0.4, 0.8), 2),
                        'support_percentage': round(influence * random.uniform(0.6, 0.95), 2),
                        'news_mentions': random.randint(0, 5),
                        'social_mentions': random.randint(1, 20),
                        'positive_mentions': random.randint(0, 5),
                        'negative_mentions': random.randint(0, 3),
                        'neutral_mentions': random.randint(0, 4),
                    },
                )
                if was_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ CandidateRegion rows: {created} new'
        ))

    # ------------------------------------------------------------------
    # News
    # ------------------------------------------------------------------

    def _seed_news(self, candidates, counties):
        for i in range(20):
            date = timezone.now() - timedelta(days=random.randint(0, 30))
            article = NewsArticle.objects.create(
                title=random.choice(NEWS_HEADLINES),
                content=f'Sample election news content, article {i + 1}.',
                summary=f'Summary of election news article {i + 1}.',
                source=random.choice(NEWS_SOURCES),
                url=f'https://example.com/news/{i}-{int(date.timestamp())}',
                published_date=date,
                sentiment_score=random.uniform(-0.3, 0.7),
                sentiment_label=random.choice(['positive', 'negative', 'neutral']),
                engagement_count=random.randint(10, 500),
                is_verified=random.choice([True, False]),
            )
            for _ in range(random.randint(1, 3)):
                article.candidates_mentioned.add(random.choice(candidates))
            for _ in range(random.randint(1, 2)):
                article.regions_mentioned.add(random.choice(counties))

        self.stdout.write(self.style.SUCCESS('✅ News articles: 20 new'))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _print_summary(self):
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('📊 Database Summary'))
        self.stdout.write(
            f'   Counties:        {Region.objects.filter(region_type="county").count()}'
        )
        self.stdout.write(
            f'   Constituencies:  {Region.objects.filter(region_type="constituency").count()}'
        )
        self.stdout.write(
            f'   Wards:           {Region.objects.filter(region_type="ward").count()}'
        )
        self.stdout.write(f'   Parties:         {Party.objects.count()}')
        self.stdout.write(f'   Candidates:      {Candidate.objects.count()}')
        self.stdout.write(f'   Influence rows:  {CandidateRegion.objects.count()}')
        self.stdout.write(f'   News articles:   {NewsArticle.objects.count()}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Done'))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  python manage.py runserver')
        self.stdout.write('  → Admin: http://localhost:8000/admin/  (admin / admin123)')
        self.stdout.write('  → API:   http://localhost:8000/api/')