import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'election_tracker.settings')
django.setup()

from django.contrib.auth.models import User
from apps.regions.models import Region
from apps.candidates.models import Party, Candidate, CandidateRegion
from apps.news.models import NewsArticle


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent / 'apps' / 'regions' / 'data'

# Nairobi, Kisumu, Mombasa, Nakuru, Uasin Gishu, Kiambu,
# Kilifi, Garissa, Kakamega, Meru  (10 demo counties)
DEMO_COUNTY_CODES = [
    'KE-01', 'KE-02', 'KE-03', 'KE-04', 'KE-05',
    'KE-06', 'KE-07', 'KE-08', 'KE-09', 'KE-10',
]

# Map from our seed codes to real counties (by name, since codes vary
# between datasets)
DEMO_COUNTY_NAMES = [
    'Nairobi', 'Kisumu', 'Mombasa', 'Nakuru', 'Uasin Gishu',
    'Kiambu', 'Kilifi', 'Garissa', 'Kakamega', 'Meru',
]

# Candidate strongholds — used to bias influence scores realistically
# so that the map doesn't look like random noise.
CANDIDATE_STRONGHOLDS = {
    'William Ruto': ['Uasin Gishu', 'Nakuru', 'Kiambu', 'Meru'],
    'Raila Odinga': ['Nairobi', 'Kisumu', 'Mombasa', 'Kakamega'],
    'Uhuru Kenyatta': ['Kiambu', 'Nairobi', 'Nakuru'],
    'Kalonzo Musyoka': ['Meru', 'Kakamega', 'Kisumu'],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(filename):
    """Load a JSON file from the data directory."""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"⚠️  Missing: {path}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def pick_county_code(county_obj):
    """
    Extract a code from a county JSON object.
    Different datasets use different keys, so we try several.
    """
    for key in ('county_code', 'code', 'COUNTY_CO', 'id', 'CODE'):
        if key in county_obj:
            return str(county_obj[key])
    return None


def pick_county_name(county_obj):
    for key in ('county_name', 'name', 'COUNTY', 'NAME_1', 'NAME'):
        if key in county_obj:
            return county_obj[key]
    return None


def pick_constituency_name(const_obj):
    for key in ('constituency_name', 'name', 'CONSTITUEN', 'NAME_2', 'NAME'):
        if key in const_obj:
            return const_obj[key]
    return None


def pick_constituency_code(const_obj, parent_code, index):
    for key in ('constituency_code', 'code', 'CONSTITUE', 'id', 'CODE'):
        if key in const_obj:
            return str(const_obj[key])
    # Fall back to a synthetic code
    return f"{parent_code}-C{index + 1:02d}"


def pick_ward_name(ward_obj):
    for key in ('ward_name', 'name', 'WARD', 'NAME_3', 'NAME'):
        if key in ward_obj:
            return ward_obj[key]
    return None


def pick_parent_code(obj):
    """Which county does this constituency/ward belong to?"""
    for key in ('county_code', 'parent_code', 'COUNTY_CO', 'county'):
        if key in obj:
            return str(obj[key])
    return None


# ---------------------------------------------------------------------------
# Step 1: Superuser
# ---------------------------------------------------------------------------

def create_superuser():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("✅ Superuser created: admin / admin123")
    else:
        print("ℹ️  Superuser already exists")


# ---------------------------------------------------------------------------
# Step 2: Parties
# ---------------------------------------------------------------------------

def create_parties():
    parties_data = [
        {'name': 'United Democratic Alliance', 'abbr': 'UDA', 'color': '#006600'},
        {'name': 'Orange Democratic Movement', 'abbr': 'ODM', 'color': '#FF6600'},
        {'name': 'Jubilee Party', 'abbr': 'JUBILEE', 'color': '#FF0000'},
        {'name': 'Wiper Democratic Movement', 'abbr': 'WIPER', 'color': '#800080'},
    ]

    parties = []
    for p in parties_data:
        party, _ = Party.objects.get_or_create(
            abbreviation=p['abbr'],
            defaults={'name': p['name'], 'color': p['color']},
        )
        parties.append(party)
        print(f"✅ Party: {party.name}")

    return parties


# ---------------------------------------------------------------------------
# Step 3: Counties, Constituencies, Wards
# ---------------------------------------------------------------------------

def load_counties_from_json():
    """
    Load county objects from the JSON dump.
    Returns a list of dicts: {code, name, lat, lng, population}
    """
    data = load_json('counties.json')
    if not data:
        return None

    # Datasets vary: top-level may be a list or a dict with 'features'
    features = data if isinstance(data, list) else data.get('features', data.get('counties', []))

    counties = []
    for obj in features:
        props = obj.get('properties', obj)
        code = pick_county_code(props)
        name = pick_county_name(props)

        if not code or not name:
            continue

        # Only keep the demo counties
        if not any(d.lower() in name.lower() for d in DEMO_COUNTY_NAMES):
            continue

        counties.append({
            'code': code,
            'name': name,
            'lat': props.get('center_lat', props.get('lat', None)),
            'lng': props.get('center_lng', props.get('lng', None)),
            'population': props.get('population', None),
        })

    return counties or None


def fallback_counties():
    """
    If counties.json is missing, use this hard-coded list.
    Matches the 10 demo counties in the frontend.
    """
    return [
        {'code': 'KE-01', 'name': 'Nairobi',    'lat': -1.286389, 'lng': 36.817223, 'population': 4397073},
        {'code': 'KE-02', 'name': 'Kisumu',     'lat': -0.091702, 'lng': 34.767956, 'population': 1134424},
        {'code': 'KE-03', 'name': 'Mombasa',    'lat': -4.043477, 'lng': 39.668206, 'population': 1208333},
        {'code': 'KE-04', 'name': 'Nakuru',     'lat': -0.303099, 'lng': 36.080026, 'population': 2162202},
        {'code': 'KE-05', 'name': 'Uasin Gishu','lat': 0.514278,  'lng': 35.269779, 'population': 1163186},
        {'code': 'KE-06', 'name': 'Kiambu',     'lat': -1.171390, 'lng': 36.835613, 'population': 2417735},
        {'code': 'KE-07', 'name': 'Kilifi',     'lat': -3.630986, 'lng': 39.849918, 'population': 1453787},
        {'code': 'KE-08', 'name': 'Garissa',    'lat': -0.456570, 'lng': 39.658407, 'population': 841353},
        {'code': 'KE-09', 'name': 'Kakamega',   'lat': 0.282731,  'lng': 34.751863, 'population': 1867946},
        {'code': 'KE-10', 'name': 'Meru',       'lat': 0.050000,  'lng': 37.650000, 'population': 1545714},
    ]


def seed_counties():
    counties = load_counties_from_json() or fallback_counties()

    seeded = []
    for c in counties:
        region, _ = Region.objects.get_or_create(
            code=c['code'],
            defaults={
                'name': c['name'],
                'region_type': 'county',
                'center_lat': c.get('lat'),
                'center_lng': c.get('lng'),
                'population': c.get('population'),
            },
        )
        seeded.append(region)
        print(f"✅ County: {region.name} ({region.code})")

    return seeded


def seed_constituencies(counties):
    """
    Create constituency records from constituencies.json if available,
    otherwise generate a small realistic set per county.
    """
    data = load_json('constituencies.json')
    created_count = 0

    if data:
        features = data if isinstance(data, list) else data.get('features', data.get('constituencies', []))

        for obj in features:
            props = obj.get('properties', obj)
            parent_code = pick_parent_code(props)
            name = pick_constituency_name(props)

            if not name or not parent_code:
                continue

            try:
                parent = Region.objects.get(code=parent_code)
            except Region.DoesNotExist:
                continue

            code = pick_constituency_code(props, parent_code, created_count)
            Region.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'region_type': 'constituency',
                    'parent': parent,
                },
            )
            created_count += 1

    # If JSON wasn't available, generate a handful per county for demo
    if created_count == 0:
        print("⚠️  constituencies.json missing — generating synthetic constituencies")
        for county in counties:
            count = random.randint(5, 12)
            for i in range(count):
                code = f"{county.code}-C{i + 1:02d}"
                Region.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': f"{county.name} Constituency {i + 1}",
                        'region_type': 'constituency',
                        'parent': county,
                    },
                )
                created_count += 1

    print(f"✅ Constituencies seeded: {created_count}")


def seed_wards():
    """
    Create ward records. Wards live under constituencies.
    """
    data = load_json('wards.json')
    created_count = 0

    if data:
        features = data if isinstance(data, list) else data.get('features', data.get('wards', []))

        # Build a lookup: constituency name -> Region
        const_lookup = {
            r.name.lower(): r for r in Region.objects.filter(region_type='constituency')
        }

        for obj in features:
            props = obj.get('properties', obj)
            name = pick_ward_name(props)
            parent_name = props.get('constituency_name') or props.get('parent_name')

            if not name or not parent_name:
                continue

            parent = const_lookup.get(parent_name.lower())
            if not parent:
                continue

            code = props.get('ward_code') or f"{parent.code}-W{created_count + 1:03d}"
            Region.objects.get_or_create(
                code=str(code),
                defaults={
                    'name': name,
                    'region_type': 'ward',
                    'parent': parent,
                },
            )
            created_count += 1

    # If JSON wasn't available, generate 5-8 wards per constituency
    if created_count == 0:
        print("⚠️  wards.json missing — generating synthetic wards")
        for constituency in Region.objects.filter(region_type='constituency'):
            count = random.randint(5, 8)
            for i in range(count):
                code = f"{constituency.code}-W{i + 1:02d}"
                Region.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': f"{constituency.name} Ward {i + 1}",
                        'region_type': 'ward',
                        'parent': constituency,
                    },
                )
                created_count += 1

    print(f"✅ Wards seeded: {created_count}")


# ---------------------------------------------------------------------------
# Step 4: Candidates
# ---------------------------------------------------------------------------

def create_candidates(parties):
    party_by_abbr = {p.abbreviation: p for p in parties}

    candidates_data = [
        {'name': 'William Ruto',   'party': 'UDA',     'position': 'president',
         'bio': 'Current President of Kenya. Former Deputy President.',
         'age': 57},
        {'name': 'Raila Odinga',   'party': 'ODM',     'position': 'president',
         'bio': 'Former Prime Minister of Kenya. Veteran opposition leader.',
         'age': 79},
        {'name': 'Uhuru Kenyatta','party': 'JUBILEE', 'position': 'president',
         'bio': 'Former President of Kenya (2013–2022).',
         'age': 62},
        {'name': 'Kalonzo Musyoka','party': 'WIPER',  'position': 'president',
         'bio': 'Former Vice President of Kenya.',
         'age': 70},
    ]

    candidates = []
    for cd in candidates_data:
        party = party_by_abbr[cd['party']]
        candidate, _ = Candidate.objects.get_or_create(
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
        print(f"✅ Candidate: {candidate.name} ({party.abbreviation})")

    return candidates


# ---------------------------------------------------------------------------
# Step 5: CandidateRegion data at every level
# ---------------------------------------------------------------------------

def influence_for(candidate_name, region_name, base_min=20, base_max=85):
    """
    Return an influence score that's biased toward the candidate's strongholds
    so the map doesn't look like random noise.
    """
    strongholds = CANDIDATE_STRONGHOLDS.get(candidate_name, [])
    is_stronghold = any(s.lower() in region_name.lower() for s in strongholds)

    if is_stronghold:
        return random.uniform(65, 92)
    return random.uniform(base_min, base_max)


def seed_candidate_regions(candidates):
    """
    For every (candidate, region) pair, create a CandidateRegion row.
    Runs at county, constituency, and ward level.
    """
    created = 0

    for candidate in candidates:
        # -- County level --
        counties = Region.objects.filter(region_type='county')
        for county in counties:
            influence = influence_for(candidate.name, county.name)
            sentiment = random.uniform(-0.4, 0.8)
            support = influence * random.uniform(0.6, 0.95)

            CandidateRegion.objects.get_or_create(
                candidate=candidate,
                region=county,
                defaults={
                    'influence_score': round(influence, 2),
                    'sentiment_score': round(sentiment, 2),
                    'support_percentage': round(support, 2),
                    'news_mentions': random.randint(5, 50),
                    'social_mentions': random.randint(20, 200),
                    'positive_mentions': random.randint(5, 30),
                    'negative_mentions': random.randint(1, 15),
                    'neutral_mentions': random.randint(5, 20),
                },
            )
            created += 1

        # -- Constituency level --
        for constituency in Region.objects.filter(region_type='constituency'):
            parent_influence = CandidateRegion.objects.filter(
                candidate=candidate,
                region=constituency.parent,
            ).first()
            base = parent_influence.influence_score if parent_influence else 50
            influence = max(0, min(100, base + random.uniform(-15, 15)))
            support = influence * random.uniform(0.6, 0.95)

            CandidateRegion.objects.get_or_create(
                candidate=candidate,
                region=constituency,
                defaults={
                    'influence_score': round(influence, 2),
                    'sentiment_score': round(random.uniform(-0.4, 0.8), 2),
                    'support_percentage': round(support, 2),
                    'news_mentions': random.randint(1, 15),
                    'social_mentions': random.randint(5, 60),
                    'positive_mentions': random.randint(1, 10),
                    'negative_mentions': random.randint(0, 5),
                    'neutral_mentions': random.randint(1, 8),
                },
            )
            created += 1

        # -- Ward level --
        for ward in Region.objects.filter(region_type='ward'):
            parent_influence = CandidateRegion.objects.filter(
                candidate=candidate,
                region=ward.parent,
            ).first()
            base = parent_influence.influence_score if parent_influence else 50
            influence = max(0, min(100, base + random.uniform(-10, 10)))

            CandidateRegion.objects.get_or_create(
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
            created += 1

    print(f"✅ CandidateRegion rows created: {created}")


# ---------------------------------------------------------------------------
# Step 6: News (unchanged, still useful for the dashboard)
# ---------------------------------------------------------------------------

def seed_news(candidates, regions):
    sources = ['Daily Nation', 'The Standard', 'Citizen TV', 'KTN News', 'KBC']
    headlines = [
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

    for i in range(20):
        date = datetime.now() - timedelta(days=random.randint(0, 30))
        article = NewsArticle.objects.create(
            title=random.choice(headlines),
            content=f"Sample election news content, article {i + 1}.",
            summary=f"Summary of election news article {i + 1}.",
            source=random.choice(sources),
            url=f"https://example.com/news/{i}-{int(date.timestamp())}",
            published_date=date,
            sentiment_score=random.uniform(-0.3, 0.7),
            sentiment_label=random.choice(['positive', 'negative', 'neutral']),
            engagement_count=random.randint(10, 500),
            is_verified=random.choice([True, False]),
        )

        for _ in range(random.randint(1, 3)):
            article.candidates_mentioned.add(random.choice(candidates))
        for _ in range(random.randint(1, 2)):
            article.regions_mentioned.add(random.choice(regions))

    print("✅ News articles created: 20")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def create_sample_data():
    print("🚀 Seeding Kenya Election Tracker...")

    create_superuser()
    parties = create_parties()
    counties = seed_counties()
    seed_constituencies(counties)
    seed_wards()
    candidates = create_candidates(parties)
    seed_candidate_regions(candidates)
    seed_news(candidates, counties)

    print("\n✅ Seeding complete")
    print(f"   Counties: {Region.objects.filter(region_type='county').count()}")
    print(f"   Constituencies: {Region.objects.filter(region_type='constituency').count()}")
    print(f"   Wards: {Region.objects.filter(region_type='ward').count()}")
    print(f"   Candidates: {Candidate.objects.count()}")
    print(f"   CandidateRegion rows: {CandidateRegion.objects.count()}")


if __name__ == '__main__':
    create_sample_data()