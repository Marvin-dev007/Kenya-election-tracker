import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_api():
    print("🧪 Testing API Endpoints...\n")
    
    # Test regions
    print("📍 Testing /regions/")
    response = requests.get(f"{BASE_URL}/regions/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Regions found: {len(data)}")
        if data:
            print(f"   First region: {data[0]['name']}")
    
    # Test candidates
    print("\n👤 Testing /candidates/")
    response = requests.get(f"{BASE_URL}/candidates/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Candidates found: {len(data)}")
        if data:
            print(f"   First candidate: {data[0]['name']}")
    
    # Test influence summary
    print("\n📊 Testing /influences/summary/")
    response = requests.get(f"{BASE_URL}/influences/summary/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total candidates: {data.get('total_candidates', 0)}")
        print(f"   Average influence: {data.get('average_influence', 0):.1f}%")
    
    # Test dashboard
    print("\n📈 Testing /dashboard/overview/")
    response = requests.get(f"{BASE_URL}/dashboard/overview/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        stats = data.get('stats', {})
        print(f"   Total candidates: {stats.get('total_candidates', 0)}")
        print(f"   Total regions: {stats.get('total_regions', 0)}")
        print(f"   Total news: {stats.get('total_news', 0)}")

if __name__ == "__main__":
    test_api()
