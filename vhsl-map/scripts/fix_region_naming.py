#!/usr/bin/env python3

import json
import os
import re

def fix_region_naming():
    """Fix region naming and classification issues in the combined GeoJSON dataset"""
    
    # Load the combined GeoJSON file
    with open('dist/data/geojson/all_schools.geojson', 'r') as f:
        all_schools_data = json.load(f)
    
    # Load the school lookup file
    with open('dist/data/geojson/school_lookup.json', 'r') as f:
        school_lookup = json.load(f)
    
    print(f"Processing {len(all_schools_data['features'])} schools...")
    
    # Fix region naming in GeoJSON features
    for feature in all_schools_data['features']:
        props = feature['properties']
        school_name = props.get('name', 'Unknown')
        class_num = props.get('size')
        region = props.get('region', '')
        
        # Check if region is in format "Region X" instead of "Region NX"
        if region and re.match(r'^Region [A-D]$', region):
            # Extract the letter part (A, B, C, D)
            region_letter = region.split(' ')[1]
            
            # Create the correct region name with class number
            if class_num:
                corrected_region = f"Region {class_num}{region_letter}"
                props['region'] = corrected_region
                print(f"Fixed {school_name}: {region} -> {corrected_region}")
    
    # Fix region naming in school lookup
    for school_name, school_data in school_lookup.items():
        region = school_data.get('region', '')
        class_num = school_data.get('size', '')
        
        # Check if region is in format "Region X" instead of "Region NX"
        if region and re.match(r'^Region [A-D]$', region):
            # Extract the letter part (A, B, C, D)
            region_letter = region.split(' ')[1]
            
            # Create the correct region name with class number
            if class_num:
                corrected_region = f"Region {class_num}{region_letter}"
                school_data['region'] = corrected_region
    
    # Save the fixed GeoJSON file
    with open('dist/data/geojson/all_schools.geojson', 'w') as f:
        json.dump(all_schools_data, f)
    
    # Save the fixed school lookup file
    with open('dist/data/geojson/school_lookup.json', 'w') as f:
        json.dump(school_lookup, f, indent=2)
    
    print("Fixed region naming in GeoJSON and lookup files")
    
    return {
        "total_schools": len(all_schools_data['features']),
        "total_lookup_entries": len(school_lookup)
    }

if __name__ == "__main__":
    print("=== Fixing Region Naming and Classification Issues ===")
    results = fix_region_naming()
    
    print("\n=== Fix Summary ===")
    print(f"Processed {results['total_schools']} schools in GeoJSON")
    print(f"Processed {results['total_lookup_entries']} entries in lookup")
    print("Region naming has been corrected to include class numbers")
