import os
import django
import requests
import re
import argparse
from django.db import transaction
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "b.settings")
django.setup()

from a.models import CelestialBody

BASE_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

def fetch_celestial_data(body_id):
    params = {
        "format": "text",
        "COMMAND": f"'{body_id}'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'500@399'",
        "START_TIME": "'2006-01-01'",
        "STOP_TIME": "'2006-01-20'",
        "STEP_SIZE": "'1 d'",
        "QUANTITIES": "'1,9,20,23,24,29'"
    }
    response = requests.get(BASE_URL, params=params)
    return response.text

def fetch_oscillating_elements(body_id):
    params = {
        "format": "text",
        "COMMAND": f"'{body_id}'",
        "EPHEM_TYPE": "ELEMENTS",
        "CENTER": "'500@10'",
        "START_TIME": "'2023-01-01'",
        "STOP_TIME": "'2023-02-01'",
        "STEP_SIZE": "'1 d'",
        "MAKE_EPHEM": "YES",
        "OUT_UNITS": "AU-D",
        "REF_PLANE": "ECLIPTIC",
        "REF_SYSTEM": "J2000",
        "TP_TYPE": "ABSOLUTE",
        "CSV_FORMAT": "NO",
        "OBJ_DATA": "YES"
    }
    response = requests.get(BASE_URL, params=params)
    return response.text

def query_object():
    body_id = input("Enter the body ID to query: ")
    print("\nSelect data type:")
    print("1. Celestial Data")
    print("2. Oscillating Elements")
    print("3. Both (Combined Result)")
    choice = input("Enter your choice (1, 2, or 3): ")

    if choice == '1':
        result = fetch_celestial_data(body_id)
        print("\nCelestial Data:")
        print(result)
    elif choice == '2':
        result = fetch_oscillating_elements(body_id)
        print("\nOscillating Elements:")
        print(result)
    elif choice == '3':
        celestial_data = fetch_celestial_data(body_id)
        oscillating_elements = fetch_oscillating_elements(body_id)
        print("\nCombined Result:")
        print("=" * 40)
        print("Celestial Data:")
        print("=" * 40)
        print(celestial_data)
        print("\n" + "=" * 40)
        print("Oscillating Elements:")
        print("=" * 40)
        print(oscillating_elements)
    else:
        print("Invalid choice. Returning to main menu.")

def parse_jpl_horizons_object_fallback(data):
    result = {}
    
    # Extract name
    name_match = re.search(r'Target body name: (.+?)\s+\(', data)
    if name_match:
        result['name'] = name_match.group(1).strip()
    
    # Extract physical characteristics
    characteristics = {
        'vol_mean_radius': r'Vol. Mean Radius \(km\)\s*=\s*([\d.]+)',
        'density': r'Density \(g cm\^-3\)\s*=\s*([\d.]+)',
        'mass': r'Mass \(10\^23 kg\)\s*=\s*([\d.]+)',
        'flattening': r'Flattening, f\s*=\s*([\d.]+)',
        'volume': r'Volume \(x10\^10 km\^3\)\s*=\s*([\d.]+)',
        'equatorial_radius': r'Equ. radius, Re \(km\)\s*=\s*([\d.]+)',
        'sidereal_rot_period': r'Sid. rot. period \(hrs\)\s*=\s*([\d.]+)',
        'sid_rot_rate': r'Sid. rot. rate \(rad/s\)\s*=\s*([\d.]+)',
        'mean_solar_day': r'Mean solar day \(s\)\s*=\s*([\d.]+)',
        'polar_gravity': r'Polar gravity ms\^-2\s*=\s*([\d.]+)',
        'core_radius': r'Core radius \(km\)\s*=\s*([\d.]+)',
        'equatorial_gravity': r'Equ. gravity  ms\^-2\s*=\s*([\d.]+)',
        'geometric_albedo': r'Geometric Albedo\s*=\s*([\d.]+)',
    }
    
    for key, pattern in characteristics.items():
        match = re.search(pattern, data)
        if match:
            result[key] = float(match.group(1))
    
    # Extract uncertainties
    uncertainties = {
        'vol_mean_radius_uncertainty': r'Vol. Mean Radius \(km\)\s*=\s*[\d.]+\s*\+-\s*([\d.]+)',
        'density_uncertainty': r'Density \(g cm\^-3\)\s*=\s*[\d.]+\s*\+-\s*([\d.]+)',
    }
    
    for key, pattern in uncertainties.items():
        match = re.search(pattern, data)
        if match:
            result[key] = float(match.group(1))
    
    # Determine body type (this is a simplification, you may need to refine this logic)
    if 'Mars' in result.get('name', ''):
        result['body_type'] = 'planet'
    else:
        result['body_type'] = 'unknown'
    
    return result

def parse_jpl_horizons_menu():
    print("\nParse JPL Horizons Object")
    print("1. Parse from file")
    print("2. Parse from query")
    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        filename = input("Enter the filename containing JPL Horizons data: ")
        try:
            with open(filename, 'r') as file:
                data = file.read()
        except FileNotFoundError:
            print(f"File '{filename}' not found.")
            return
    elif choice == '2':
        body_id = input("Enter the body ID to query: ")
        data = fetch_celestial_data(body_id) + "\n" + fetch_oscillating_elements(body_id)
    else:
        print("Invalid choice. Returning to main menu.")
        return

    parsed_data = parse_jpl_horizons_object_fallback(data)
    print("\nParsed Data:")
    for key, value in parsed_data.items():
        print(f"{key}: {value}")

def update_celestial_body():
    print("\nUpdate Celestial Body")
    start_id = input("Enter the starting body ID to update: ")
    end_id = input("Enter the ending body ID to update (press Enter if updating only one body): ")
    
    if end_id == "":
        end_id = start_id
    
    try:
        start_id = int(start_id)
        end_id = int(end_id)
    except ValueError:
        print("Invalid input. Please enter numeric ID values.")
        return

    if start_id > end_id:
        start_id, end_id = end_id, start_id

    for body_id in range(start_id, end_id + 1):
        print(f"\nProcessing body ID: {body_id}")
        
        # Fetch data from JPL Horizons
        try:
            celestial_data = fetch_celestial_data(str(body_id))
            oscillating_elements = fetch_oscillating_elements(str(body_id))
            combined_data = celestial_data + "\n" + oscillating_elements
        except Exception as e:
            print(f"Error fetching data for body ID {body_id}: {str(e)}")
            continue
        
        # Parse the data
        parsed_data = parse_jpl_horizons_object_fallback(combined_data)
        
        if 'name' not in parsed_data:
            print(f"Could not parse name for body ID {body_id}. Skipping.")
            continue
        
        # Check if the celestial body exists in the database
        celestial_body, created = CelestialBody.objects.get_or_create(name=parsed_data['name'])
        
        if created:
            print(f"Created new entry for {parsed_data['name']}")
        else:
            print(f"Updating existing entry for {parsed_data['name']}")
        
        # Update the celestial body with parsed data
        for key, value in parsed_data.items():
            if hasattr(celestial_body, key):
                setattr(celestial_body, key, value)
        
        # Save the updated or new celestial body
        celestial_body.save()
        print(f"Successfully updated/created entry for {celestial_body.name}")

def view_celestial_body():
    print("\nView Celestial Body")
    body_name = input("Enter the name of the celestial body to view: ")
    
    try:
        celestial_body = CelestialBody.objects.get(name=body_name)
        print(f"\nData for {celestial_body.name}:")
        
        # Get all fields of the model
        fields = CelestialBody._meta.fields
        
        for field in fields:
            value = getattr(celestial_body, field.name)
            if value is not None:
                print(f"{field.verbose_name}: {value}")
        
    except CelestialBody.DoesNotExist:
        print(f"No entry found for {body_name}")

def main_menu():
    while True:
        print("\nMain Menu:")
        print("1. Query JPL Horizons Object")
        print("2. Parse JPL Horizons Object")
        print("3. Update Celestial Body/Bodies")
        print("4. View Celestial Body")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            query_object()
        elif choice == '2':
            parse_jpl_horizons_menu()
        elif choice == '3':
            update_celestial_body()
        elif choice == '4':
            view_celestial_body()
        elif choice == '5':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()