#!/usr/bin/env python3

import json
import os
import glob

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def main():
    # Load the compiled schools data from GeoJSON files
    compiled_data = load_json_file('data/compiled_schools.json')
    if not compiled_data:
        print("Failed to load compiled schools data")
        return
    
    # Load the current application data
    vhsl_classes_regions = load_json_file('data/vhsl_classes_regions.json')
    vhsl_districts = load_json_file('data/vhsl_districts.json')
    va_schools_geocodes = load_json_file('data/va_schools_geocodes.json')
    
    if not all([vhsl_classes_regions, vhsl_districts, va_schools_geocodes]):
        print("Failed to load one or more application data files")
        return
    
    # Check if all schools from GeoJSON are in the application data
    geojson_schools = set(compiled_data['all_schools'])
    app_schools = set()
    
    # Extract schools from va_schools_geocodes.json
    for school in va_schools_geocodes.get('schools', []):
        app_schools.add(school.get('name', ''))
    
    # Find missing schools
    missing_in_app = geojson_schools - app_schools
    missing_in_geojson = app_schools - geojson_schools
    
    print(f"\n=== VALIDATION RESULTS ===")
    print(f"Schools in GeoJSON files: {len(geojson_schools)}")
    print(f"Schools in application data: {len(app_schools)}")
    print(f"Schools in GeoJSON but missing in app: {len(missing_in_app)}")
    if missing_in_app:
        print("Examples of missing schools:")
        for school in list(missing_in_app)[:10]:  # Show first 10 examples
            print(f"  - {school}")
    
    print(f"Schools in app but not in GeoJSON: {len(missing_in_geojson)}")
    if missing_in_geojson:
        print("Examples of extra schools:")
        for school in list(missing_in_geojson)[:10]:  # Show first 10 examples
            print(f"  - {school}")
    
    # Check class distribution
    print("\n=== CLASS DISTRIBUTION ===")
    print("In GeoJSON files:")
    for class_num, schools in compiled_data['by_class'].items():
        print(f"  Class {class_num}: {len(schools)} schools")
    
    # Check if the application has proper class filtering
    print("\n=== CLASS FILTERING CHECK ===")
    classes_in_app = {}
    for class_info in vhsl_classes_regions.get('classes', []):
        class_num = class_info.get('id', '').replace('class', '')
        classes_in_app[class_num] = []
        
        # Count schools in each region of this class
        for region in class_info.get('regions', []):
            region_id = region.get('id', '')
            region_schools = []
            
            # We would need to check which schools are assigned to this region
            # This would require additional data structure or logic
            
            classes_in_app[class_num].extend(region_schools)
    
    print("Classes defined in application:")
    for class_num, schools in classes_in_app.items():
        print(f"  Class {class_num}: {len(schools)} schools")
    
    # Create a mapping file to help with integration
    mapping_data = {
        "school_mapping": {},
        "class_mapping": {},
        "region_mapping": {},
        "district_mapping": {}
    }
    
    # Extract school information from GeoJSON files
    for file in glob.glob('data/geojson/schools_by_region/*.geojson'):
        filename = os.path.basename(file)
        region_name = filename.replace('.geojson', '')
        class_num = region_name.split(' ')[1][0]
        
        with open(file) as f:
            data = json.load(f)
            for feature in data['features']:
                if 'properties' in feature and 'name' in feature['properties']:
                    school_name = feature['properties']['name']
                    district = feature['properties'].get('district', 'Unknown')
                    
                    # Store mapping information
                    mapping_data["school_mapping"][school_name] = {
                        "class": class_num,
                        "region": region_name,
                        "district": district,
                        "coordinates": feature.get('geometry', {}).get('coordinates', [])
                    }
    
    # Save the mapping data
    with open('data/school_mapping.json', 'w') as f:
        json.dump(mapping_data, f, indent=2)
    
    print("\nSchool mapping data saved to data/school_mapping.json")
    
    # Provide recommendations
    print("\n=== RECOMMENDATIONS ===")
    if missing_in_app:
        print("1. Update the application data to include all schools from the GeoJSON files")
    if len(compiled_data['by_class']) > len(classes_in_app):
        print("2. Ensure all classes (1-6) are properly defined in the application")
    print("3. Verify that the class filtering functionality is correctly implemented")
    print("4. Use the generated school_mapping.json to update school classifications")

if __name__ == "__main__":
    main()
