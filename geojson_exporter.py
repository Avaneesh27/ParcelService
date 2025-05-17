import json

def create_geojson(places, path, output_file="route.geojson"):
    """
    Create a GeoJSON LineString representing the path
    """
    # Extract coordinates for the path
    coordinates = [[places[i].lon, places[i].lat] for i in path]
    
    # Create GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                }
            }
        ]
    }
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    return output_file