import csv
import math
import json
import argparse
from collections import namedtuple

# Define a Place namedtuple to store location information
Place = namedtuple('Place', ['name', 'lat', 'lon'])

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def create_distance_matrix(places):
    """Create a distance matrix for the given places"""
    n = len(places)
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = haversine(
                    places[i].lat, places[i].lon,
                    places[j].lat, places[j].lon
                )
    
    return matrix

def greedy_tsp(distance_matrix, start_index=0):
    """
    Greedy algorithm for TSP:
    1. Start at the specified index
    2. Repeatedly visit the nearest unvisited place
    """
    n = len(distance_matrix)
    visited = [False] * n
    path = [start_index]
    visited[start_index] = True
    
    # Visit all remaining places
    for _ in range(n - 1):
        current = path[-1]
        next_place = None
        min_distance = float('inf')
        
        for candidate in range(n):
            if not visited[candidate] and distance_matrix[current][candidate] < min_distance:
                next_place = candidate
                min_distance = distance_matrix[current][candidate]
        
        path.append(next_place)
        visited[next_place] = True
    
    return path

def calculate_path_distance(path, distance_matrix):
    """Calculate the total distance of a path"""
    total = 0
    for i in range(len(path) - 1):
        total += distance_matrix[path[i]][path[i + 1]]
    return total

def two_opt_swap(path, i, j):
    """Perform a 2-opt swap by reversing the segment between i and j"""
    new_path = path[:i]
    new_path.extend(reversed(path[i:j + 1]))
    new_path.extend(path[j + 1:])
    return new_path

def two_opt_improvement(path, distance_matrix):
    """
    2-opt improvement algorithm:
    Try all possible 2-opt swaps and apply if they improve the solution
    """
    improved = True
    best_path = path
    best_distance = calculate_path_distance(path, distance_matrix)
    
    while improved:
        improved = False
        for i in range(1, len(best_path) - 2):
            for j in range(i + 1, len(best_path) - 1):
                new_path = two_opt_swap(best_path, i, j)
                new_distance = calculate_path_distance(new_path, distance_matrix)
                
                if new_distance < best_distance:
                    best_path = new_path
                    best_distance = new_distance
                    improved = True
                    break
            if improved:
                break
    
    return best_path

def solve_tsp(distance_matrix, start_index=0, return_to_start=False):
    """
    Solve the TSP using greedy algorithm followed by 2-opt improvement
    """
    # Get initial solution using greedy algorithm
    path = greedy_tsp(distance_matrix, start_index)
    
    # Improve solution using 2-opt
    path = two_opt_improvement(path, distance_matrix)
    
    # Add the start point at the end if return_to_start is True
    if return_to_start:
        path.append(start_index)
    
    return path

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

def read_places_from_csv(csv_file):
    """Read places from a CSV file"""
    places = []
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:  # Ensure we have name, lat, lon
                try:
                    name = row[0]
                    lat = float(row[1])
                    lon = float(row[2])
                    places.append(Place(name, lat, lon))
                except ValueError:
                    # Skip header or invalid rows
                    continue
    return places

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Travelling Salesman Problem Solver')
    parser.add_argument('--csv', required=True, help='CSV file with places (Name,Lat,Lon)')
    parser.add_argument('--start', help='Name of the starting place')
    parser.add_argument('--return', dest='return_to_start', action='store_true', 
                        help='Return to the starting place')
    parser.add_argument('--output', default='route.geojson', 
                        help='Output GeoJSON file (default: route.geojson)')
    
    args = parser.parse_args()
    
    # Read places from CSV
    places = read_places_from_csv(args.csv)
    if not places:
        print("Error: No valid places found in the CSV file.")
        return
    
    # Find start index
    start_index = 0
    if args.start:
        for i, place in enumerate(places):
            if place.name == args.start:
                start_index = i
                break
        else:
            print(f"Warning: Start place '{args.start}' not found. Using first place instead.")
    
    # Create distance matrix
    distance_matrix = create_distance_matrix(places)
    
    # Solve TSP
    path = solve_tsp(distance_matrix, start_index, args.return_to_start)
    
    # Calculate total distance
    total_distance = calculate_path_distance(path, distance_matrix)
    
    # Print results
    print(f"Optimal tour {'(returns to start)' if args.return_to_start else ''}:")
    for i, idx in enumerate(path):
        print(f"{i+1}) {places[idx].name}")
    
    print(f"Total distance: {total_distance:.1f} km")
    
    # Export to GeoJSON
    output_file = create_geojson(places, path, args.output)
    print(f"Route written to {output_file}")

if __name__ == "__main__":
    main()