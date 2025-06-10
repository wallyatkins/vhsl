#!/usr/bin/env python3

import json
import os

def verify_schools_integration():
    """Verify the integration of all schools in the combined dataset"""
    
    # Load the combined GeoJSON file
    with open('dist/data/geojson/all_schools.geojson', 'r') as f:
        all_schools_data = json.load(f)
    
    # Load the school lookup file
    with open('dist/data/geojson/school_lookup.json', 'r') as f:
        school_lookup = json.load(f)
    
    # Count schools by class
    classes = {}
    for feature in all_schools_data['features']:
        class_num = feature['properties'].get('size')
        if class_num not in classes:
            classes[class_num] = 0
        classes[class_num] += 1
    
    # Print summary
    print(f"Total features in all_schools.geojson: {len(all_schools_data['features'])}")
    print(f"Total schools in school_lookup.json: {len(school_lookup)}")
    
    print("\nSchools by class:")
    for class_num in sorted(classes.keys()):
        print(f"Class {class_num}: {classes[class_num]} schools")
    
    # Verify all schools have required properties
    missing_properties = []
    for feature in all_schools_data['features']:
        props = feature['properties']
        school_name = props.get('name')
        
        if not school_name:
            missing_properties.append("Missing name")
            continue
            
        if 'size' not in props:
            missing_properties.append(f"{school_name}: Missing size")
        
        if 'region' not in props:
            missing_properties.append(f"{school_name}: Missing region")
            
        if 'district' not in props:
            missing_properties.append(f"{school_name}: Missing district")
    
    if missing_properties:
        print("\nMissing properties:")
        for issue in missing_properties[:10]:  # Show first 10 issues
            print(f"- {issue}")
        if len(missing_properties) > 10:
            print(f"... and {len(missing_properties) - 10} more issues")
    else:
        print("\nAll schools have required properties")
    
    # Verify all schools in lookup match GeoJSON
    geojson_schools = set(feature['properties'].get('name') for feature in all_schools_data['features'] if feature['properties'].get('name'))
    lookup_schools = set(school_lookup.keys())
    
    missing_in_geojson = lookup_schools - geojson_schools
    missing_in_lookup = geojson_schools - lookup_schools
    
    if missing_in_geojson:
        print("\nSchools in lookup but missing in GeoJSON:")
        for school in list(missing_in_geojson)[:10]:
            print(f"- {school}")
        if len(missing_in_geojson) > 10:
            print(f"... and {len(missing_in_geojson) - 10} more")
    
    if missing_in_lookup:
        print("\nSchools in GeoJSON but missing in lookup:")
        for school in list(missing_in_lookup)[:10]:
            print(f"- {school}")
        if len(missing_in_lookup) > 10:
            print(f"... and {len(missing_in_lookup) - 10} more")
    
    if not missing_in_geojson and not missing_in_lookup:
        print("\nAll schools match between GeoJSON and lookup")
    
    return {
        "total_schools": len(all_schools_data['features']),
        "schools_by_class": classes,
        "missing_properties": len(missing_properties),
        "missing_in_geojson": len(missing_in_geojson),
        "missing_in_lookup": len(missing_in_lookup)
    }

if __name__ == "__main__":
    print("=== Verifying School Integration ===")
    results = verify_schools_integration()
    
    print("\n=== Integration Summary ===")
    if (results["total_schools"] == 319 and 
        results["missing_properties"] == 0 and 
        results["missing_in_geojson"] == 0 and 
        results["missing_in_lookup"] == 0):
        print("✅ All checks passed! Dataset is complete and consistent.")
    else:
        print("❌ Some issues were found in the dataset.")
