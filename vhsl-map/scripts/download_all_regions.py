#!/usr/bin/env python3

import os
import requests
import json
from pathlib import Path

def download_all_region_files():
    """Download all region GeoJSON files from GitHub repository"""
    
    # Base URL for the GitHub repository
    base_url = "https://raw.githubusercontent.com/wallyatkins/vhsl/main/geojson/vhsl_regions/schools_by_region/"
    
    # Create directories if they don't exist
    dist_geojson_dir = Path("/home/ubuntu/vhsl-map-project/dist/data/geojson")
    data_geojson_dir = Path("/home/ubuntu/vhsl-map-project/data/geojson/schools_by_region")
    
    os.makedirs(dist_geojson_dir, exist_ok=True)
    os.makedirs(data_geojson_dir, exist_ok=True)
    
    # Generate all region file names (Classes 1-6, Regions A-D)
    region_files = []
    for class_num in range(1, 7):
        for region_letter in ['A', 'B', 'C', 'D']:
            region_name = f"Region {class_num}{region_letter}"
            region_files.append(region_name)
    
    print(f"Downloading {len(region_files)} region files...")
    
    # Download each file
    downloaded_files = []
    for region in region_files:
        # Format URL with proper encoding for spaces
        url = f"{base_url}{region.replace(' ', '%20')}.geojson"
        
        # Format filenames for saving
        dist_filename = f"{dist_geojson_dir}/Region_{region.split(' ')[1]}.geojson"
        data_filename = f"{data_geojson_dir}/{region}.geojson"
        
        print(f"Downloading {region} from {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Save to dist directory
            with open(dist_filename, 'w') as f:
                f.write(response.text)
                
            # Save to data directory
            with open(data_filename, 'w') as f:
                f.write(response.text)
                
            downloaded_files.append(region)
            print(f"  Success: Saved to {dist_filename} and {data_filename}")
            
        except Exception as e:
            print(f"  Error downloading {region}: {str(e)}")
    
    print(f"Downloaded {len(downloaded_files)} out of {len(region_files)} region files")
    return downloaded_files

def update_all_schools_geojson():
    """Combine all region files into a single all_schools.geojson file"""
    
    dist_geojson_dir = Path("/home/ubuntu/vhsl-map-project/dist/data/geojson")
    data_geojson_dir = Path("/home/ubuntu/vhsl-map-project/data/geojson/schools_by_region")
    
    # Output file paths
    all_schools_file = dist_geojson_dir / "all_schools.geojson"
    
    # Initialize combined GeoJSON
    combined = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Track unique schools to avoid duplicates
    unique_schools = set()
    
    # Process all region files
    region_files = list(data_geojson_dir.glob("*.geojson"))
    print(f"Combining {len(region_files)} region files...")
    
    feature_id = 1
    for file_path in region_files:
        region_name = file_path.stem
        print(f"Processing {region_name}...")
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for feature in data.get('features', []):
                # Extract school name
                school_name = feature.get('properties', {}).get('name')
                
                if school_name and school_name not in unique_schools:
                    # Add unique ID to feature
                    feature['id'] = feature_id
                    feature_id += 1
                    
                    # Add to combined features
                    combined['features'].append(feature)
                    unique_schools.add(school_name)
        except Exception as e:
            print(f"  Error processing {file_path}: {str(e)}")
    
    # Save combined GeoJSON
    with open(all_schools_file, 'w') as f:
        json.dump(combined, f)
    
    print(f"Combined GeoJSON saved to {all_schools_file}")
    print(f"Total unique schools: {len(unique_schools)}")
    
    return len(unique_schools)

def update_school_lookup():
    """Update the school lookup file based on the combined GeoJSON"""
    
    dist_geojson_dir = Path("/home/ubuntu/vhsl-map-project/dist/data/geojson")
    
    # Input and output files
    all_schools_file = dist_geojson_dir / "all_schools.geojson"
    lookup_file = dist_geojson_dir / "school_lookup.json"
    
    # Load combined GeoJSON
    with open(all_schools_file, 'r') as f:
        data = json.load(f)
    
    # Create lookup dictionary
    lookup = {}
    
    for feature in data.get('features', []):
        properties = feature.get('properties', {})
        school_name = properties.get('name')
        
        if school_name:
            # Extract class number from region (e.g., "Region 1A" -> "1")
            region = properties.get('region', '')
            class_num = region.split(' ')[1][0] if region and ' ' in region and len(region.split(' ')[1]) > 0 else ''
            
            lookup[school_name] = {
                'name': school_name,
                'size': class_num,
                'class': f"Class {class_num}" if class_num else '',
                'region': properties.get('region', ''),
                'district': properties.get('district', '')
            }
    
    # Save lookup file
    with open(lookup_file, 'w') as f:
        json.dump(lookup, f, indent=2)
    
    print(f"School lookup saved to {lookup_file}")
    print(f"Total schools in lookup: {len(lookup)}")
    
    return len(lookup)

def verify_all_regions_present():
    """Verify that all 24 region files are present"""
    
    dist_geojson_dir = Path("/home/ubuntu/vhsl-map-project/dist/data/geojson")
    
    # Check for all expected region files
    expected_regions = []
    for class_num in range(1, 7):
        for region_letter in ['A', 'B', 'C', 'D']:
            expected_regions.append(f"Region_{class_num}{region_letter}.geojson")
    
    missing_regions = []
    for region in expected_regions:
        if not (dist_geojson_dir / region).exists():
            missing_regions.append(region)
    
    if missing_regions:
        print(f"Missing {len(missing_regions)} region files:")
        for region in missing_regions:
            print(f"  {region}")
        return False
    else:
        print(f"All {len(expected_regions)} region files are present")
        return True

if __name__ == "__main__":
    print("=== Downloading and Processing VHSL Region Files ===")
    
    # Step 1: Download all region files
    downloaded_files = download_all_region_files()
    
    # Step 2: Verify all regions are present
    all_present = verify_all_regions_present()
    
    if all_present:
        # Step 3: Update all_schools.geojson
        school_count = update_all_schools_geojson()
        
        # Step 4: Update school lookup
        lookup_count = update_school_lookup()
        
        print("\n=== Summary ===")
        print(f"Downloaded {len(downloaded_files)} region files")
        print(f"Combined {school_count} unique schools")
        print(f"Created lookup with {lookup_count} schools")
        print("\nProcessing complete!")
    else:
        print("\n=== Error ===")
        print("Some region files are missing. Please check the errors above.")
