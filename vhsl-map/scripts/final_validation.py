#!/usr/bin/env python3

import json
import os

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def main():
    print("=== FINAL VALIDATION ===")
    
    # Load the updated application data files
    va_schools = load_json_file('data/va_schools_geocodes.json')
    classes_regions = load_json_file('data/vhsl_classes_regions.json')
    districts = load_json_file('data/vhsl_districts.json')
    
    if not all([va_schools, classes_regions, districts]):
        print("Failed to load one or more application data files")
        return
    
    # Validate schools data
    schools = va_schools.get('schools', [])
    print(f"Total schools in dataset: {len(schools)}")
    
    # Count schools by class
    schools_by_class = {}
    for school in schools:
        class_num = school.get('class', 'Unknown')
        if class_num not in schools_by_class:
            schools_by_class[class_num] = []
        schools_by_class[class_num].append(school.get('name', 'Unknown'))
    
    print("\n=== SCHOOLS BY CLASS ===")
    for class_num in sorted(schools_by_class.keys()):
        print(f"Class {class_num}: {len(schools_by_class[class_num])} schools")
    
    # Validate classes and regions
    classes = classes_regions.get('classes', [])
    print(f"\nTotal classes defined: {len(classes)}")
    
    for class_info in classes:
        class_id = class_info.get('id', '')
        class_name = class_info.get('name', '')
        regions = class_info.get('regions', [])
        print(f"{class_name} ({class_id}): {len(regions)} regions")
    
    # Validate districts
    district_list = districts.get('districts', [])
    print(f"\nTotal districts defined: {len(district_list)}")
    
    total_district_schools = 0
    for district in district_list:
        district_name = district.get('name', '')
        district_schools = district.get('schools', [])
        total_district_schools += len(district_schools)
        print(f"{district_name}: {len(district_schools)} schools")
    
    print(f"\nTotal schools in districts: {total_district_schools}")
    
    # Final validation summary
    print("\n=== VALIDATION SUMMARY ===")
    print(f"Schools in dataset: {len(schools)}")
    print(f"Classes defined: {len(classes)}")
    print(f"Districts defined: {len(district_list)}")
    
    # Check for any remaining issues
    issues = []
    
    # Check if all classes (1-6) are defined
    defined_classes = [c.get('name', '').replace('Class ', '') for c in classes]
    for expected_class in ['1', '2', '3', '4', '5', '6']:
        if expected_class not in defined_classes:
            issues.append(f"Class {expected_class} is not defined in classes_regions.json")
    
    # Check if all schools have class, region, and district information
    for school in schools:
        if 'class' not in school or not school['class']:
            issues.append(f"School {school.get('name', 'Unknown')} is missing class information")
        if 'region' not in school or not school['region']:
            issues.append(f"School {school.get('name', 'Unknown')} is missing region information")
        if 'district' not in school or not school['district']:
            issues.append(f"School {school.get('name', 'Unknown')} is missing district information")
    
    if issues:
        print("\n=== REMAINING ISSUES ===")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"- {issue}")
        if len(issues) > 10:
            print(f"... and {len(issues) - 10} more issues")
    else:
        print("\nNo issues found. Data validation successful!")

if __name__ == "__main__":
    main()
