#!/usr/bin/env python3

import json
import os
from collections import defaultdict

def validate_district_region_class():
    """Validate schools across districts, regions, and classes"""
    
    # Load the combined GeoJSON file
    with open('dist/data/geojson/all_schools.geojson', 'r') as f:
        all_schools_data = json.load(f)
    
    # Initialize counters
    schools_by_class = defaultdict(list)
    schools_by_region = defaultdict(list)
    schools_by_district = defaultdict(list)
    
    # Collect schools by classification
    for feature in all_schools_data['features']:
        props = feature['properties']
        school_name = props.get('name', 'Unknown')
        class_num = props.get('size')
        region = props.get('region')
        district = props.get('district')
        
        if class_num:
            schools_by_class[class_num].append(school_name)
        
        if region:
            schools_by_region[region].append(school_name)
        
        if district:
            schools_by_district[district].append(school_name)
    
    # Print summary
    print("=== Validation by Classification ===")
    
    print("\n--- Schools by Class ---")
    for class_num in sorted(schools_by_class.keys()):
        schools = schools_by_class[class_num]
        print(f"Class {class_num}: {len(schools)} schools")
    
    print("\n--- Schools by Region ---")
    for region in sorted(schools_by_region.keys()):
        schools = schools_by_region[region]
        print(f"{region}: {len(schools)} schools")
    
    print("\n--- Schools by District ---")
    for district in sorted(schools_by_district.keys()):
        schools = schools_by_district[district]
        print(f"{district}: {len(schools)} schools")
    
    # Validate class-region consistency
    print("\n=== Validating Class-Region Consistency ===")
    class_region_issues = []
    
    for region, schools in schools_by_region.items():
        if not region or ' ' not in region:
            class_region_issues.append(f"Invalid region format: {region}")
            continue
            
        expected_class = region.split(' ')[1][0]
        
        for school_name in schools:
            # Find the school in the features
            school_feature = next((f for f in all_schools_data['features'] 
                                if f['properties'].get('name') == school_name), None)
            
            if not school_feature:
                class_region_issues.append(f"School {school_name} not found in features")
                continue
                
            school_class = school_feature['properties'].get('size')
            
            if str(school_class) != str(expected_class):
                class_region_issues.append(
                    f"School {school_name} has class {school_class} but is in region {region} (expected class {expected_class})"
                )
    
    if class_region_issues:
        print("Issues found:")
        for issue in class_region_issues[:10]:
            print(f"- {issue}")
        if len(class_region_issues) > 10:
            print(f"... and {len(class_region_issues) - 10} more issues")
    else:
        print("✅ All schools have consistent class-region assignments")
    
    # Validate statewide coverage
    print("\n=== Validating Statewide Coverage ===")
    
    # Check if all expected regions are present (Classes 1-6, Regions A-D)
    expected_regions = [f"Region {c}{r}" for c in range(1, 7) for r in ['A', 'B', 'C', 'D']]
    missing_regions = [r for r in expected_regions if r not in schools_by_region]
    
    if missing_regions:
        print("Missing regions:")
        for region in missing_regions:
            print(f"- {region}")
    else:
        print("✅ All expected regions are present")
    
    # Return validation results
    return {
        "total_schools": len(all_schools_data['features']),
        "classes": len(schools_by_class),
        "regions": len(schools_by_region),
        "districts": len(schools_by_district),
        "class_region_issues": len(class_region_issues),
        "missing_regions": len(missing_regions)
    }

if __name__ == "__main__":
    print("=== Running Validation Checks ===")
    results = validate_district_region_class()
    
    print("\n=== Validation Summary ===")
    print(f"Total schools: {results['total_schools']}")
    print(f"Classes: {results['classes']}")
    print(f"Regions: {results['regions']}")
    print(f"Districts: {results['districts']}")
    
    if (results["class_region_issues"] == 0 and 
        results["missing_regions"] == 0):
        print("✅ All validation checks passed!")
    else:
        print("❌ Some validation issues were found.")
