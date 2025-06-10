#!/usr/bin/env python3

import json
import os
import glob
import requests
from collections import defaultdict

def download_geojson_files():
    """Download all GeoJSON files from GitHub repository"""
    base_url = "https://raw.githubusercontent.com/wallyatkins/vhsl/main/geojson/vhsl_regions/schools_by_region/"
    output_dir = "data/geojson/schools_by_region"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # List of all region files to download
    regions = []
    for class_num in range(1, 7):  # Classes 1-6
        for region_letter in ['A', 'B', 'C', 'D']:  # Regions A-D
            regions.append(f"Region {class_num}{region_letter}")
    
    print(f"Downloading {len(regions)} region files...")
    
    # Download each file
    for region in regions:
        url = f"{base_url}{region.replace(' ', '%20')}.geojson"
        output_file = f"{output_dir}/{region}.geojson"
        
        print(f"Downloading {region}...")
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            with open(output_file, 'w') as f:
                f.write(response.text)
            print(f"  Success: {output_file}")
        except Exception as e:
            print(f"  Error downloading {region}: {str(e)}")
    
    return regions

def combine_geojson_files():
    """Combine all downloaded GeoJSON files into a single file"""
    input_dir = "data/geojson/schools_by_region"
    output_file = "dist/data/geojson/all_schools.geojson"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Initialize combined GeoJSON
    combined = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Track unique schools to avoid duplicates
    unique_schools = set()
    
    # Process all GeoJSON files
    files = glob.glob(f"{input_dir}/*.geojson")
    print(f"Combining {len(files)} GeoJSON files...")
    
    feature_id = 1
    for file_path in files:
        region_name = os.path.basename(file_path).replace('.geojson', '')
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
    with open(output_file, 'w') as f:
        json.dump(combined, f)
    
    print(f"Combined GeoJSON saved to {output_file}")
    print(f"Total unique schools: {len(unique_schools)}")
    
    return combined

def create_school_lookup():
    """Create a lookup file for school information"""
    input_file = "dist/data/geojson/all_schools.geojson"
    output_file = "dist/data/geojson/school_lookup.json"
    
    # Load combined GeoJSON
    with open(input_file, 'r') as f:
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
    with open(output_file, 'w') as f:
        json.dump(lookup, f, indent=2)
    
    print(f"School lookup saved to {output_file}")
    print(f"Total schools in lookup: {len(lookup)}")
    
    return lookup

def main():
    print("=== VHSL GeoJSON Download and Processing ===")
    
    # Step 1: Download all GeoJSON files
    regions = download_geojson_files()
    
    # Step 2: Combine all GeoJSON files
    combined = combine_geojson_files()
    
    # Step 3: Create school lookup
    lookup = create_school_lookup()
    
    print("\n=== Summary ===")
    print(f"Downloaded {len(regions)} region files")
    print(f"Combined {len(combined['features'])} unique schools")
    print(f"Created lookup with {len(lookup)} schools")
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()
