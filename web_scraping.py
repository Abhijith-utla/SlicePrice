import requests
import os
import json
from datetime import datetime
import time
import math

SERPAPI_API_KEY = "9bdb9d8d83a93b38fa2eb16730baa6fe5a1fd399a8d8b5e371ff5bae70ce561d"

# SauceBros location coordinates (will be populated by geocode function)
SAUCEBROS_LAT = None
SAUCEBROS_LNG = None

def geocode_address(address):
    """Convert address to latitude/longitude coordinates using a geocoding service."""
    try:
        # Using Google Maps Geocoding API through SerpAPI
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps",
            "q": address,
            "type": "search",
            "api_key": SERPAPI_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if "place_results" in data and "gps_coordinates" in data["place_results"]:
            coords = data["place_results"]["gps_coordinates"]
            return coords.get("latitude"), coords.get("longitude")
            
        # Fallback to approximate coordinates for Plano, TX 75023
        print("⚠️ Could not geocode the address. Using default coordinates for Plano, TX 75023")
        return 33.0482, -96.7298
    except Exception as e:
        print(f"❌ Error geocoding address: {e}")
        # Return default coordinates for Plano, TX 75023
        return 33.0482, -96.7298

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points using Haversine formula."""
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = 6371 * c  # Earth radius in km
    
    return distance

def search_nearby_restaurants(latitude, longitude, radius_km=5, limit=20):
    """Search for restaurants near the specified coordinates."""
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps",
            "q": "restaurants",
            "ll": f"{latitude},{longitude}",  # Fixed parameter format
            "lq": f"{latitude},{longitude},{radius_km}km",  # Added lq parameter with radius
            "type": "search",
            "api_key": SERPAPI_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        local_results = data.get("local_results", [])
        
        if not local_results:
            print(f"⚠️ No nearby restaurants found within {radius_km}km")
            return []
            
        # Add the distance to each restaurant
        for restaurant in local_results:
            if "gps_coordinates" in restaurant:
                rest_lat = restaurant["gps_coordinates"]["latitude"]
                rest_lng = restaurant["gps_coordinates"]["longitude"]
                restaurant["distance"] = calculate_distance(latitude, longitude, rest_lat, rest_lng)
            else:
                restaurant["distance"] = 999  # Default high distance for sorting
        
        # Sort by distance and return requested limit
        sorted_restaurants = sorted(local_results, key=lambda x: x.get("distance", 999))
        return sorted_restaurants[:limit]
    except Exception as e:
        print(f"❌ Error searching for nearby restaurants: {e}")
        return []

def search_restaurant_by_name(name, location="Plano, TX"):
    """Search for a specific restaurant by name and location."""
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "yelp",
            "find_desc": name,
            "find_loc": location,
            "api_key": SERPAPI_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("organic_results", [])
        
        if not results:
            print(f"⚠️ Restaurant '{name}' not found")
            return None
            
        # Return the first result which is usually the most relevant
        return results[0]
    except requests.exceptions.RequestException as e:
        print(f"❌ Error searching for restaurant '{name}': {e}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error parsing data for restaurant '{name}'")
        return None

def get_google_reviews(place_id):
    """Get reviews from Google Maps for a specific place_id."""
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "api_key": SERPAPI_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        reviews = data.get("reviews", [])
        
        if not reviews:
            print(f"⚠️ No Google reviews found for place_id: {place_id}")
        
        return reviews
    except Exception as e:
        print(f"❌ Error fetching Google reviews: {e}")
        return []

def get_yelp_reviews(place_id, max_pages=10):
    """Get all available reviews from Yelp for a specific place_id."""
    all_reviews = []
    page = 1
    
    # SerpAPI often limits to 10 reviews per page, so we need to paginate
    while page <= max_pages:  # Limit to max_pages to avoid excessive API calls
        try:
            url = "https://serpapi.com/search.json"
            params = {
                "engine": "yelp_reviews",
                "place_id": place_id,
                "page": page,
                "api_key": SERPAPI_API_KEY
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            reviews = data.get("reviews", [])
            
            if not reviews:
                break  # No more reviews to fetch
            
            all_reviews.extend(reviews)
            print(f"  📄 Page {page}: found {len(reviews)} reviews")
            page += 1
            
            # Respect rate limits
            if page <= max_pages:
                time.sleep(1)  # Add a delay between requests
                
        except Exception as e:
            print(f"❌ Error fetching reviews page {page}: {e}")
            break
    
    if not all_reviews:
        print(f"⚠️ No reviews found for place_id: {place_id}")
    else:
        print(f"📊 Total: {len(all_reviews)} reviews from {page-1} pages")
        
    return all_reviews

def format_review_data(review, source="yelp"):
    """Extract relevant data from a review object based on source."""
    if source == "yelp":
        formatted = {
            "user": review.get("user", {}).get("name", "Anonymous"),
            "rating": review.get("rating", "N/A"),
            "date": review.get("date", "N/A"),
            "text": review.get("comment", {}).get("text") if isinstance(review.get("comment"), dict) else review.get("snippet", "No text")
        }
    else:  # google
        formatted = {
            "user": review.get("user", {}).get("name", "Anonymous"),
            "rating": review.get("rating", "N/A"),
            "date": review.get("date", "N/A"),
            "text": review.get("snippet", "No text")
        }
    return formatted

def save_reviews_to_txt(restaurant_name, reviews, address="", source="yelp"):
    """Save reviews to a text file."""
    os.makedirs("restaurant_reviews", exist_ok=True)
    filename = f"{restaurant_name.replace(' ', '_').replace('/', '_')}_{source}_reviews.txt"
    filepath = os.path.join("restaurant_reviews", filename)
    
    saved_count = 0
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Restaurant: {restaurant_name}\n")
        if address:
            f.write(f"Address: {address}\n")
        f.write(f"Source: {source.capitalize()}\n")
        f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        for review in reviews:
            formatted = format_review_data(review, source)
            
            if not formatted["text"] or formatted["text"].strip() == "":
                continue  # Skip reviews with no text
                
            f.write(f"Reviewer: {formatted['user']}\n")
            f.write(f"Rating: {formatted['rating']} stars\n")
            f.write(f"Date: {formatted['date']}\n")
            f.write(f"Review: {formatted['text']}\n")
            f.write("-" * 60 + "\n\n")
            saved_count += 1
    
    if saved_count > 0:
        print(f"✅ Saved {saved_count} {source.capitalize()} reviews for {restaurant_name}: {filename}")
    else:
        print(f"⚠️ No valid text reviews to save for {restaurant_name}")
        os.remove(filepath)  # Remove empty file
    
    return saved_count

def main():
    print("🍕 Starting restaurant review collector focused on SauceBros Pizza")
    
    # First, get SauceBros info
    saucebros = search_restaurant_by_name("SauceBros Pizza", "Plano, TX")
    if not saucebros:
        print("❌ Could not find SauceBros Pizza. Exiting.")
        return
    
    saucebros_name = saucebros.get("title", "SauceBros Pizza")
    saucebros_address = saucebros.get("address", "3115 W Parker Rd Ste #570, Plano, TX 75023")
    place_id = None
    
    if "place_ids" in saucebros and saucebros["place_ids"]:
        place_id = saucebros["place_ids"][0]
    elif "place_id" in saucebros:
        place_id = saucebros["place_id"]
    
    print(f"🔍 Found SauceBros Pizza: {saucebros_name}")
    print(f"📍 Address: {saucebros_address}")
    
    # Geocode SauceBros address to get coordinates
    global SAUCEBROS_LAT, SAUCEBROS_LNG
    SAUCEBROS_LAT, SAUCEBROS_LNG = geocode_address(saucebros_address)
    print(f"📌 SauceBros coordinates: {SAUCEBROS_LAT}, {SAUCEBROS_LNG}")
    
    # First, get reviews for SauceBros
    if place_id:
        print(f"\n🔄 Fetching all available reviews for SauceBros Pizza...")
        reviews = get_yelp_reviews(place_id)
        save_reviews_to_txt(saucebros_name, reviews, saucebros_address)
    else:
        print("⚠️ Could not find place_id for SauceBros Pizza")
    
    # Now find the 10 closest restaurants
    print(f"\n🔍 Searching for 10 restaurants closest to SauceBros Pizza...")
    nearby_restaurants = search_nearby_restaurants(SAUCEBROS_LAT, SAUCEBROS_LNG, radius_km=3, limit=15)
    
    if not nearby_restaurants:
        print("❌ No nearby restaurants found. Exiting.")
        return
    
    # Create a list that excludes SauceBros itself
    other_restaurants = []
    for restaurant in nearby_restaurants:
        name = restaurant.get("title")
        if name and "SauceBros" not in name and "Sauce Bros" not in name:
            other_restaurants.append(restaurant)
    
    closest_restaurants = other_restaurants[:10]  # Get 10 closest (excluding SauceBros)
    print(f"📍 Found {len(closest_restaurants)} restaurants close to SauceBros Pizza")
    
    # Get reviews for each nearby restaurant
    for i, restaurant in enumerate(closest_restaurants, 1):
        name = restaurant.get("title", f"Restaurant-{i}")
        address = restaurant.get("address", "Address not available")
        distance = restaurant.get("distance", "unknown")
        
        print(f"\n🔍 ({i}/{len(closest_restaurants)}) Getting reviews for: {name}")
        print(f"📍 Address: {address}")
        print(f"📏 Distance from SauceBros: {distance:.2f} km")
        
        # Get Google Maps place_id
        place_id = restaurant.get("place_id")
        if place_id:
            print(f"🔄 Fetching all available Google Maps reviews...")
            reviews = get_google_reviews(place_id)
            save_reviews_to_txt(name, reviews, address, source="google")
        else:
            print("⚠️ No Google Maps place_id found")
        
        # Try to find on Yelp as well
        print(f"🔄 Searching for {name} on Yelp...")
        yelp_result = search_restaurant_by_name(name, "Plano, TX")
        if yelp_result:
            yelp_place_id = None
            if "place_ids" in yelp_result and yelp_result["place_ids"]:
                yelp_place_id = yelp_result["place_ids"][0]
            elif "place_id" in yelp_result:
                yelp_place_id = yelp_result["place_id"]
                
            if yelp_place_id:
                print(f"🔄 Fetching all available Yelp reviews...")
                yelp_reviews = get_yelp_reviews(yelp_place_id)
                save_reviews_to_txt(name, yelp_reviews, address, source="yelp")
            else:
                print("⚠️ No Yelp place_id found")
        else:
            print(f"⚠️ Could not find {name} on Yelp")
        
        # Add a delay between restaurants to respect rate limits
        if i < len(closest_restaurants):
            time.sleep(2)

    print("\n✅ Review collection complete!")

if __name__ == "__main__":
    main()