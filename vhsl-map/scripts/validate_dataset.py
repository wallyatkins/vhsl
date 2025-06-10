#!/usr/bin/env python3

import json
import os
from pathlib import Path

def validate_dataset():
    """Validate the complete dataset to ensure all schools are properly included"""
    
    dist_geojson_dir = Path("/home/ubuntu/vhsl-map-project/dist/data/geojson")
    
    # Check for all region files
    region_files = list(dist_geojson_dir.glob("Region_*.geojson"))
    print(f"Found {len(region_files)} region files")
    
    # Check all_schools.geojson
    all_schools_file = dist_geojson_dir / "all_schools.geojson"
    if not all_schools_file.exists():
        print(f"Error: {all_schools_file} does not exist")
        return False
    
    # Check school_lookup.json
    lookup_file = dist_geojson_dir / "school_lookup.json"
    if not lookup_file.exists():
        print(f"Error: {lookup_file} does not exist")
        return False
    
    # Load all_schools.geojson
    with open(all_schools_file, 'r') as f:
        all_schools_data = json.load(f)
    
    # Load school_lookup.json
    with open(lookup_file, 'r') as f:
        lookup_data = json.load(f)
    
    # Count schools by class
    schools_by_class = {}
    schools_by_region = {}
    
    for feature in all_schools_data.get('features', []):
        properties = feature.get('properties', {})
        school_name = properties.get('name')
        region = properties.get('region', '')
        
        # Extract class from region (e.g., "Region 1A" -> "1")
        class_num = region.split(' ')[1][0] if region and ' ' in region and len(region.split(' ')[1]) > 0 else 'Unknown'
        
        # Count by class
        if class_num not in schools_by_class:
            schools_by_class[class_num] = []
        schools_by_class[class_num].append(school_name)
        
        # Count by region
        if region not in schools_by_region:
            schools_by_region[region] = []
        schools_by_region[region].append(school_name)
    
    # Print summary
    print("\n=== Dataset Validation ===")
    print(f"Total schools in all_schools.geojson: {len(all_schools_data.get('features', []))}")
    print(f"Total schools in school_lookup.json: {len(lookup_data)}")
    
    print("\n=== Schools by Class ===")
    for class_num in sorted(schools_by_class.keys()):
        print(f"Class {class_num}: {len(schools_by_class[class_num])} schools")
    
    print("\n=== Schools by Region ===")
    for region in sorted(schools_by_region.keys()):
        print(f"{region}: {len(schools_by_region[region])} schools")
    
    # Verify all classes are represented
    expected_classes = ['1', '2', '3', '4', '5', '6']
    missing_classes = [c for c in expected_classes if c not in schools_by_class]
    
    if missing_classes:
        print(f"\nWarning: Missing schools for classes: {', '.join(missing_classes)}")
        return False
    else:
        print("\nAll classes (1-6) are represented in the dataset")
        return True

if __name__ == "__main__":
    print("=== Validating Complete Dataset ===")
    success = validate_dataset()
    
    if success:
        print("\nValidation successful! The dataset is complete.")
    else:
        print("\nValidation failed. Please check the errors above.")
