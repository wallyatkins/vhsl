#!/usr/bin/env python3

import json
import os
from pathlib import Path

def fix_class_region_assignment():
    """Fix class and region assignments in the combined GeoJSON and lookup files"""
    
    dist_geojson_dir = Path("/home/ubuntu/vhsl-map-project/dist/data/geojson")
    
    # Load all_schools.geojson
    all_schools_file = dist_geojson_dir / "all_schools.geojson"
    with open(all_schools_file, 'r') as f:
        all_schools_data = json.load(f)
    
    # Load school_lookup.json
    lookup_file = dist_geojson_dir / "school_lookup.json"
    with open(lookup_file, 'r') as f:
        lookup_data = json.load(f)
    
    print(f"Fixing class and region assignments for {len(all_schools_data.get('features', []))} schools...")
    
    # Fix region and class assignments in all_schools.geojson
    for feature in all_schools_data.get('features', []):
        properties = feature.get('properties', {})
        region = properties.get('region', '')
        
        # Check if region follows the pattern "Region X" where X is A, B, C, or D
        if region and region.startswith('Region ') and len(region) > 7:
            region_letter = region[7:]  # Extract "A", "B", "C", or "D"
            
            # Determine class number from filename
            for class_num in range(1, 7):
                if f"Region {class_num}{region_letter}" in properties.get('_source_file', ''):
                    # Update region to include class number
                    properties['region'] = f"Region {class_num}{region_letter}"
                    # Add class property
                    properties['class'] = f"Class {class_num}"
                    # Add size property (numeric class)
                    properties['size'] = str(class_num)
                    break
            
            # If we couldn't determine class from filename, try to infer from other schools in the same region
            if 'class' not in properties and '_source_file' in properties:
                source_file = properties.get('_source_file', '')
                if 'Region_' in source_file:
                    class_region = source_file.split('Region_')[1].split('.')[0]
                    if len(class_region) >= 2:
                        class_num = class_region[0]
                        if class_num.isdigit():
                            properties['region'] = f"Region {class_num}{region_letter}"
                            properties['class'] = f"Class {class_num}"
                            properties['size'] = class_num
    
    # Save updated all_schools.geojson
    with open(all_schools_file, 'w') as f:
        json.dump(all_schools_data, f)
    
    print(f"Updated all_schools.geojson with fixed class and region assignments")
    
    # Fix lookup data
    updated_lookup = {}
    
    for school_name, school_data in lookup_data.items():
        region = school_data.get('region', '')
        
        # Find matching feature in all_schools_data
        matching_feature = None
        for feature in all_schools_data.get('features', []):
            if feature.get('properties', {}).get('name') == school_name:
                matching_feature = feature
                break
        
        if matching_feature:
            properties = matching_feature.get('properties', {})
            updated_lookup[school_name] = {
                'name': school_name,
                'size': properties.get('size', ''),
                'class': properties.get('class', ''),
                'region': properties.get('region', ''),
                'district': properties.get('district', '')
            }
        else:
            # Keep original data if no match found
            updated_lookup[school_name] = school_data
    
    # Save updated lookup
    with open(lookup_file, 'w') as f:
        json.dump(updated_lookup, f, indent=2)
    
    print(f"Updated school_lookup.json with fixed class and region assignments")
    
    return len(updated_lookup)

def extract_class_from_region_files():
    """Extract class information from region filenames and update the combined dataset"""
    
    dist_geojson_dir = Path("/home/ubuntu/vhsl-map-project/dist/data/geojson")
    data_geojson_dir = Path("/home/ubuntu/vhsl-map-project/data/geojson/schools_by_region")
    
    # Create a mapping of school names to their correct class and region
    school_mapping = {}
    
    # Process all region files to extract class information
    for class_num in range(1, 7):
        for region_letter in ['A', 'B', 'C', 'D']:
            region_file = data_geojson_dir / f"Region {class_num}{region_letter}.geojson"
            
            if region_file.exists():
                try:
                    with open(region_file, 'r') as f:
                        data = json.load(f)
                    
                    for feature in data.get('features', []):
                        school_name = feature.get('properties', {}).get('name')
                        if school_name:
                            school_mapping[school_name] = {
                                'class': f"Class {class_num}",
                                'size': str(class_num),
                                'region': f"Region {class_num}{region_letter}"
                            }
                except Exception as e:
                    print(f"Error processing {region_file}: {str(e)}")
    
    print(f"Extracted class and region information for {len(school_mapping)} schools")
    
    # Update all_schools.geojson with the correct class and region information
    all_schools_file = dist_geojson_dir / "all_schools.geojson"
    with open(all_schools_file, 'r') as f:
        all_schools_data = json.load(f)
    
    for feature in all_schools_data.get('features', []):
        school_name = feature.get('properties', {}).get('name')
        if school_name and school_name in school_mapping:
            feature['properties']['class'] = school_mapping[school_name]['class']
            feature['properties']['size'] = school_mapping[school_name]['size']
            feature['properties']['region'] = school_mapping[school_name]['region']
    
    # Save updated all_schools.geojson
    with open(all_schools_file, 'w') as f:
        json.dump(all_schools_data, f)
    
    print(f"Updated all_schools.geojson with correct class and region information")
    
    # Update school_lookup.json with the correct class and region information
    lookup_file = dist_geojson_dir / "school_lookup.json"
    with open(lookup_file, 'r') as f:
        lookup_data = json.load(f)
    
    for school_name, school_data in lookup_data.items():
        if school_name in school_mapping:
            school_data['class'] = school_mapping[school_name]['class']
            school_data['size'] = school_mapping[school_name]['size']
            school_data['region'] = school_mapping[school_name]['region']
    
    # Save updated lookup
    with open(lookup_file, 'w') as f:
        json.dump(lookup_data, f, indent=2)
    
    print(f"Updated school_lookup.json with correct class and region information")
    
    return len(school_mapping)

if __name__ == "__main__":
    print("=== Fixing Class and Region Assignments ===")
    
    # Extract class information from region files
    num_schools_extracted = extract_class_from_region_files()
    
    # Fix class and region assignments
    num_schools_fixed = fix_class_region_assignment()
    
    print("\n=== Summary ===")
    print(f"Extracted class information for {num_schools_extracted} schools")
    print(f"Fixed class and region assignments for {num_schools_fixed} schools")
    print("\nProcessing complete!")
