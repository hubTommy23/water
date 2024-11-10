from flask import Flask, request, jsonify, render_template
import requests
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_water_quality')
def get_water_quality():
    zip_code = request.args.get('zipCode')
    
    # Validate the ZIP code format (only allow 5-digit ZIP codes)
    if not re.match(r'^\d{5}$', zip_code):
        return jsonify({"error": "Invalid ZIP code format. Please enter a 5-digit ZIP code."}), 400
    
    # Step 1: Use Zippopotam.us to get latitude and longitude
    geocode_url = f"http://api.zippopotam.us/us/{zip_code}"
    
    try:
        geocode_response = requests.get(geocode_url)
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()
        
        # Extract latitude and longitude
        latitude = float(geocode_data['places'][0]['latitude'])
        longitude = float(geocode_data['places'][0]['longitude'])
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"An error occurred while fetching data: {str(e)}"}), 500
    except (KeyError, IndexError):
        return jsonify({"error": "No data found for this ZIP code."}), 404

    # Step 2: Define a bounding box around the coordinates
    radius_degrees = 0.1  # Adjust this value to expand or contract the search area
    min_lat = latitude - radius_degrees
    max_lat = latitude + radius_degrees
    min_lon = longitude - radius_degrees
    max_lon = longitude + radius_degrees
    
    # Query the Water Quality Portal API using the bounding box
    wqp_url = "https://www.waterqualitydata.us/data/Station/search"
    params = {
        "bBox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "mimeType": "geojson"
    }
    headers = {
        "Accept": "application/json"
    }

    try:
        wqp_response = requests.get(wqp_url, params=params, headers=headers)
        wqp_response.raise_for_status()
        wqp_data = wqp_response.json()
        
        # Prepare the data for the frontend
        if 'features' in wqp_data:
            sites = []
            for site in wqp_data['features']:
                properties = site.get('properties', {})
                sites.append({
                    "monitoringLocationName": properties.get("MonitoringLocationName", "N/A"),
                    "organizationIdentifier": properties.get("OrganizationIdentifier", "N/A"),
                    "monitoringLocationTypeName": properties.get("MonitoringLocationTypeName", "N/A"),
                    "latitude": properties.get("LatitudeMeasure", "N/A"),
                    "longitude": properties.get("LongitudeMeasure", "N/A")
                })
            return jsonify(sites)
        else:
            return jsonify([])  # No sites found
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"An error occurred while fetching data: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)