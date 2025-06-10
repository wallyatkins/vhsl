#!/usr/bin/env python3

import json
import os
import glob
from collections import defaultdict

def main():
    # Initialize data structures
    all_schools = []
    schools_by_class = defaultdict(list)
    schools_by_region = defaultdict(list)
    schools_by_district = defaultdict(list)
    
    # Process all GeoJSON files
    geojson_files = glob.glob('data/geojson/schools_by_region/*.geojson')
    print(f"Found {len(geojson_files)} GeoJSON files")
    
    for file in geojson_files:
        filename = os.path.basename(file)
        region_name = filename.replace('.geojson', '')
        class_num = region_name.split(' ')[1][0]  # Extract class number (1-6)
        region_letter = region_name.split(' ')[1][1]  # Extract region letter (A-D)
        
        print(f"Processing {filename}...")
        
        try:
            with open(file) as f:
                data = json.load(f)
                
                if 'features' not in data:
                    print(f"WARNING: No features found in {filename}")
                    continue
                
                for feature in data['features']:
                    if 'properties' in feature and 'name' in feature['properties']:
                        school_name = feature['properties']['name']
                        district = feature['properties'].get('district', 'Unknown')
                        
                        # Add to collections
                        all_schools.append(school_name)
                        schools_by_class[class_num].append(school_name)
                        schools_by_region[region_name].append(school_name)
                        schools_by_district[district].append(school_name)
                    else:
                        print(f"WARNING: Missing properties or name in a feature in {filename}")
        except Exception as e:
            print(f"ERROR processing {filename}: {str(e)}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Total schools found: {len(all_schools)}")
    print(f"Unique schools: {len(set(all_schools))}")
    
    print("\n=== SCHOOLS BY CLASS ===")
    for class_num in sorted(schools_by_class.keys()):
        schools = schools_by_class[class_num]
        print(f"Class {class_num}: {len(schools)} schools ({len(set(schools))} unique)")
    
    print("\n=== SCHOOLS BY REGION ===")
    for region in sorted(schools_by_region.keys()):
        schools = schools_by_region[region]
        print(f"{region}: {len(schools)} schools ({len(set(schools))} unique)")
    
    print("\n=== SCHOOLS BY DISTRICT ===")
    for district in sorted(schools_by_district.keys()):
        schools = schools_by_district[district]
        print(f"{district}: {len(schools)} schools ({len(set(schools))} unique)")
    
    # Save the compiled data for further use
    compiled_data = {
        "all_schools": list(set(all_schools)),
        "by_class": {k: list(set(v)) for k, v in schools_by_class.items()},
        "by_region": {k: list(set(v)) for k, v in schools_by_region.items()},
        "by_district": {k: list(set(v)) for k, v in schools_by_district.items()}
    }
    
    with open('data/compiled_schools.json', 'w') as f:
        json.dump(compiled_data, f, indent=2)
    
    print("\nCompiled data saved to data/compiled_schools.json")

if __name__ == "__main__":
    main()
