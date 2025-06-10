#!/usr/bin/env python3

import json
import os
import glob
from collections import defaultdict

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def save_json_file(file_path, data):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully saved {file_path}")
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {str(e)}")
        return False

def main():
    print("Starting application data update...")
    
    # Load the school mapping data created by the comparison script
    school_mapping = load_json_file('data/school_mapping.json')
    if not school_mapping or 'school_mapping' not in school_mapping:
        print("Failed to load school mapping data")
        return
    
    # Extract school information from GeoJSON files
    schools_by_class = defaultdict(list)
    schools_by_region = defaultdict(list)
    schools_by_district = defaultdict(list)
    all_schools = []
    
    # Process all schools from the mapping
    for school_name, info in school_mapping['school_mapping'].items():
        class_num = info['class']
        region_name = info['region']
        district = info['district']
        coordinates = info['coordinates']
        
        # Skip if coordinates are missing
        if not coordinates or len(coordinates) < 2:
            print(f"Warning: Missing coordinates for {school_name}")
            continue
        
        # Create school entry
        school_entry = {
            "name": school_name,
            "coordinates": {
                "lng": coordinates[0],
                "lat": coordinates[1]
            },
            "address": f"{school_name}, Virginia",
            "class": class_num,
            "region": region_name,
            "district": district,
            "synthetic": False
        }
        
        all_schools.append(school_entry)
        schools_by_class[class_num].append(school_name)
        schools_by_region[region_name].append(school_name)
        schools_by_district[district].append(school_name)
    
    # Create updated va_schools_geocodes.json
    va_schools_data = {
        "schools": all_schools
    }
    save_json_file('data/va_schools_geocodes_updated.json', va_schools_data)
    
    # Create updated vhsl_classes_regions.json
    classes_regions_data = {
        "classes": []
    }
    
    for class_num in sorted(schools_by_class.keys()):
        class_entry = {
            "id": f"class{class_num}",
            "name": f"Class {class_num}",
            "regions": []
        }
        
        # Add regions for this class
        for region_name in sorted(schools_by_region.keys()):
            if region_name.startswith(f"Region {class_num}"):
                region_letter = region_name.split(' ')[1][1]
                region_entry = {
                    "id": f"region{class_num}{region_letter}",
                    "name": region_name
                }
                class_entry["regions"].append(region_entry)
        
        classes_regions_data["classes"].append(class_entry)
    
    save_json_file('data/vhsl_classes_regions_updated.json', classes_regions_data)
    
    # Create updated vhsl_districts.json
    districts_data = {
        "districts": []
    }
    
    for district_name in sorted(schools_by_district.keys()):
        if district_name == "Unknown":
            continue
            
        district_entry = {
            "id": district_name.lower().replace(' ', '_'),
            "name": district_name,
            "schools": schools_by_district[district_name]
        }
        districts_data["districts"].append(district_entry)
    
    save_json_file('data/vhsl_districts_updated.json', districts_data)
    
    print("\n=== UPDATE SUMMARY ===")
    print(f"Total schools processed: {len(all_schools)}")
    print(f"Classes: {len(classes_regions_data['classes'])}")
    print(f"Districts: {len(districts_data['districts'])}")
    
    print("\nUpdated data files created:")
    print("- data/va_schools_geocodes_updated.json")
    print("- data/vhsl_classes_regions_updated.json")
    print("- data/vhsl_districts_updated.json")
    
    print("\nTo apply these updates, rename the files to replace the originals:")
    print("mv data/va_schools_geocodes_updated.json data/va_schools_geocodes.json")
    print("mv data/vhsl_classes_regions_updated.json data/vhsl_classes_regions.json")
    print("mv data/vhsl_districts_updated.json data/vhsl_districts.json")

if __name__ == "__main__":
    main()
