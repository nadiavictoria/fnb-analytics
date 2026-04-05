import os
import glob
import pandas as pd
import re
import urllib.parse
import requests 
import time

# --- CONFIGURATION ---
API_KEY = "xxx" # Replace this with your api key
CSV_FOLDER = "csv" # Replace this with your folder

# --- FUNCTIONS ---
def get_postal_from_url(url, api_key):
    """Extracts place name from URL and gets postal code via Google Places API."""
    if not isinstance(url, str) or not url.strip():
        return None
        
    try:
        match = re.search(r'/(?:place|search)/([^/]+)', urllib.parse.unquote(url))
        if not match: return None
        
        gmaps = googlemaps.Client(key=api_key) # pyright: ignore[reportUndefinedVariable]
        query = match.group(1).replace('+', ' ')
        
        place = gmaps.find_place(query, 'textquery', fields=['place_id'])
        if not place.get('candidates'): return None
        
        details = gmaps.place(place['candidates'][0]['place_id'], fields=['address_component'])
        for comp in details['result'].get('address_components',[]):
            if 'postal_code' in comp['types']:
                return comp['long_name']
    except Exception:
        return None
    return None

def get_coordinates(postal_code):
    """Takes a postal code, queries OneMap API, and returns (lon, lat)."""
    if not postal_code:
        return None, None
        
    url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={postal_code}&returnGeom=Y&getAddrDetails=N&pageNum=1"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data['found'] > 0:
            # Extract longitude and latitude in that exact order
            lon = float(data['results'][0]['LONGITUDE'])
            lat = float(data['results'][0]['LATITUDE'])
            return lon, lat
    except Exception as e:
        print(f"  [!] Error fetching coordinates for {postal_code}: {e}")
    return None, None

# --- MAIN SCRIPT ---
def process_csv_files():
    # Find all CSV files in the folder
    csv_files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in the '{CSV_FOLDER}' directory.")
        return

    for file_path in csv_files:
        print(f"\nProcessing: {file_path}")
        
        # Read the CSV
        df = pd.read_csv(file_path)
        
        # Check if 'url' column exists
        if 'url' not in df.columns:
            print(f"  [Skipping] 'url' column not found in {file_path}")
            continue
            
        # Create columns if they don't exist yet
        for col in ['postal', 'lon', 'lat']:
            if col not in df.columns:
                df[col] = None
                
        # Iterate through rows
        for index, row in df.iterrows():
            url = row['url']
            
            # Skip if the postal code is already filled (useful if the script crashes and you restart it)
            if pd.notna(row['postal']) and pd.notna(row['lon']):
                continue
                
            postal = get_postal_from_url(url, API_KEY)
            
            if postal:
                lon, lat = get_coordinates(postal)
                
                # Update the DataFrame
                df.at[index, 'postal'] = postal
                df.at[index, 'lon'] = lon
                df.at[index, 'lat'] = lat
                
                print(f"  Row {index}: Found Postal {postal} -> Lon: {lon}, Lat: {lat}")
            else:
                print(f"  Row {index}: Could not extract postal code.")
            
            # Brief pause to respect API rate limits
            time.sleep(0.1)
            
        # Save the updated DataFrame back to the same CSV file
        df.to_csv(file_path, index=False)
        print(f"Successfully updated and saved {file_path}")

if __name__ == "__main__":
    process_csv_files()