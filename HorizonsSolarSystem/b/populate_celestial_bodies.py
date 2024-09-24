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
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch data for body ID {body_id}")
        return None

def parse_celestial_data(data):
    parsed_data = {}
    
    def extract_float(pattern, text):
        match = re.search(pattern, text)
        return float(match.group(1)) if match else None

    name_match = re.search(r'Target body name: (.+?) \(', data)
    parsed_data['name'] = name_match.group(1) if name_match else None

    # Physical characteristics
    parsed_data['vol_mean_radius'] = extract_float(r'Vol\. mean radius \(km\) = ([\d.]+)', data)
    parsed_data['vol_mean_radius_uncertainty'] = extract_float(r'Vol\. mean radius \(km\) = [\d.]+\+-?([\d.]+)', data)
    parsed_data['density'] = extract_float(r'Density \(g/cm\^3\)\s+=\s+([\d.]+)', data)
    parsed_data['density_uncertainty'] = extract_float(r'Density \(g/cm\^3\)\s+=\s+[\d.]+\(5\+-?([\d]+)\)', data)
    parsed_data['mass'] = extract_float(r'Mass x10\^23 \(kg\)\s+=\s+([\d.]+)', data)
    parsed_data['flattening'] = extract_float(r'Flattening, f\s+=\s+1/([\d.]+)', data)
    parsed_data['volume'] = extract_float(r'Volume \(x10\^10 km\^3\)\s+=\s+([\d.]+)', data)
    parsed_data['equatorial_radius'] = extract_float(r'Equatorial radius \(km\)=\s+([\d.]+)', data)
    parsed_data['sidereal_rot_period'] = extract_float(r'Sidereal rot\. period\s+=\s+([\d.]+)', data)
    parsed_data['sid_rot_rate'] = extract_float(r'Sid\. rot\. rate, rad/s =\s+([\d.]+)', data)
    parsed_data['mean_solar_day'] = extract_float(r'Mean solar day \(sol\)\s+=\s+([\d.]+)', data)
    parsed_data['polar_gravity'] = extract_float(r'Polar gravity m/s\^2\s+=\s+([\d.]+)', data)
    parsed_data['core_radius'] = extract_float(r'Core radius \(km\)\s+=\s+~([\d.]+)', data)
    parsed_data['equatorial_gravity'] = extract_float(r'Equ\. gravity\s+m/s\^2\s+=\s+([\d.]+)', data)
    parsed_data['geometric_albedo'] = extract_float(r'Geometric Albedo\s+=\s+([\d.]+)', data)

    # Gravitational characteristics
    parsed_data['gm'] = extract_float(r'GM \(km\^3/s\^2\)\s+=\s+([\d.]+)', data)
    parsed_data['gm_uncertainty'] = extract_float(r'GM 1-sigma \(km\^3/s\^2\) = \+- ([\d.]+)', data)
    parsed_data['mass_ratio_to_sun'] = extract_float(r'Mass ratio \(Sun/[^)]+\) = ([\d.]+)', data)
    
    # Atmospheric characteristics
    atmos_mass_match = re.search(r'Mass of atmosphere, kg= ~ ([\d.]+) x 10\^(\d+)', data)
    if atmos_mass_match:
        parsed_data['atmosphere_mass'] = float(atmos_mass_match.group(1)) * (10 ** int(atmos_mass_match.group(2)))
    parsed_data['mean_temperature'] = extract_float(r'Mean temperature \(K\)\s+=\s+([\d.]+)', data)
    parsed_data['surface_pressure'] = extract_float(r'Atmos\. pressure \(bar\)\s+=\s+([\d.]+)', data)

    # Orbital characteristics
    parsed_data['obliquity_to_orbit'] = extract_float(r'Obliquity to orbit\s+=\s+([\d.]+)', data)
    parsed_data['max_angular_diameter'] = extract_float(r'Max\. angular diam\.\s+=\s+([\d.]+)', data)
    parsed_data['mean_sidereal_orbit_period_years'] = extract_float(r'Mean sidereal orb per =\s+([\d.]+)', data)
    parsed_data['mean_sidereal_orbit_period_days'] = extract_float(r'Mean sidereal orb per =\s+[\d.]+ y\s+([\d.]+)', data)
    parsed_data['visual_magnitude'] = extract_float(r'Visual mag\. V\(1,0\)\s+=\s+([-\d.]+)', data)
    parsed_data['orbital_speed'] = extract_float(r'Orbital speed,\s+km/s\s+=\s+([\d.]+)', data)
    parsed_data['hill_sphere_radius'] = extract_float(r'Hill\'s sphere rad\. Rp =\s+([\d.]+)', data)
    parsed_data['escape_speed'] = extract_float(r'Escape speed, km/s\s+=\s+([\d.]+)', data)

    # Solar interaction
    solar_match = re.search(r'Solar Constant \(W/m\^2\)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', data)
    if solar_match:
        parsed_data['solar_constant_perihelion'] = float(solar_match.group(1))
        parsed_data['solar_constant_aphelion'] = float(solar_match.group(2))
        parsed_data['solar_constant_mean'] = float(solar_match.group(3))

    ir_match = re.search(r'Maximum Planetary IR \(W/m\^2\)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', data)
    if ir_match:
        parsed_data['max_planetary_ir_perihelion'] = float(ir_match.group(1))
        parsed_data['max_planetary_ir_aphelion'] = float(ir_match.group(2))
        parsed_data['max_planetary_ir_mean'] = float(ir_match.group(3))

    parsed_data['min_planetary_ir'] = extract_float(r'Minimum Planetary IR \(W/m\^2\)\s+([\d.]+)', data)

    # Tertiary Information
    parsed_data['target_pole_equ'] = re.search(r'Target pole/equ : (.+)', data).group(1) if re.search(r'Target pole/equ : (.+)', data) else None
    
    radii_match = re.search(r'Target radii\s+:\s+([\d.]+),\s+([\d.]+),\s+([\d.]+)', data)
    if radii_match:
        parsed_data['target_radii_a'] = float(radii_match.group(1))
        parsed_data['target_radii_b'] = float(radii_match.group(2))
        parsed_data['target_radii_c'] = float(radii_match.group(3))

    center_match = re.search(r'Center geodetic\s+:\s+([-\d.]+),\s+([-\d.]+),\s+([-\d.]+)', data)
    if center_match:
        parsed_data['center_geodetic_lon'] = float(center_match.group(1))
        parsed_data['center_geodetic_lat'] = float(center_match.group(2))
        parsed_data['center_geodetic_alt'] = float(center_match.group(3))

    center_cyl_match = re.search(r'Center cylindric: ([-\d.]+),\s+([-\d.]+),\s+([-\d.]+)', data)
    if center_cyl_match:
        parsed_data['center_cylindric_lon'] = float(center_cyl_match.group(1))
        parsed_data['center_cylindric_dxy'] = float(center_cyl_match.group(2))
        parsed_data['center_cylindric_dz'] = float(center_cyl_match.group(3))

    parsed_data['center_pole_equ'] = re.search(r'Center pole/equ : (.+)', data).group(1) if re.search(r'Center pole/equ : (.+)', data) else None

    center_radii_match = re.search(r'Center radii\s+:\s+([\d.]+),\s+([\d.]+),\s+([\d.]+)', data)
    if center_radii_match:
        parsed_data['center_radii_a'] = float(center_radii_match.group(1))
        parsed_data['center_radii_b'] = float(center_radii_match.group(2))
        parsed_data['center_radii_c'] = float(center_radii_match.group(3))

    parsed_data['target_primary'] = re.search(r'Target primary\s+:\s+(.+)', data).group(1) if re.search(r'Target primary\s+:\s+(.+)', data) else None
    parsed_data['vis_interferer'] = re.search(r'Vis\. interferer : (.+?) \(', data).group(1) if re.search(r'Vis\. interferer : (.+?) \(', data) else None
    parsed_data['vis_interferer_radius'] = extract_float(r'Vis\. interferer : .+? \(R_eq= ([\d.]+)', data)
    parsed_data['rel_light_bend'] = re.search(r'Rel\. light bend : (.+)', data).group(1) if re.search(r'Rel\. light bend : (.+)', data) else None
    parsed_data['rel_light_bend_gm'] = extract_float(r'Rel\. lght bnd GM: ([\d.E+]+)', data)
    parsed_data['atmos_refraction'] = re.search(r'Atmos refraction: (.+)', data).group(1) if re.search(r'Atmos refraction: (.+)', data) else None
    parsed_data['ra_format'] = re.search(r'RA format\s+: (.+)', data).group(1) if re.search(r'RA format\s+: (.+)', data) else None
    parsed_data['time_format'] = re.search(r'Time format\s+: (.+)', data).group(1) if re.search(r'Time format\s+: (.+)', data) else None
    parsed_data['calendar_mode'] = re.search(r'Calendar mode\s+: (.+)', data).group(1) if re.search(r'Calendar mode\s+: (.+)', data) else None
    parsed_data['eop_file'] = re.search(r'EOP file\s+: (.+)', data).group(1) if re.search(r'EOP file\s+: (.+)', data) else None

    eop_coverage_match = re.search(r'EOP coverage\s+:\s+(.+)\s+TO\s+(.+)\.', data)
    if eop_coverage_match:
        parsed_data['eop_coverage_start'] = parse_date(eop_coverage_match.group(1))
        parsed_data['eop_coverage_end'] = parse_date(eop_coverage_match.group(2))

    eop_predict_match = re.search(r'EOP PREDICTS-> (.+)', data)
    if eop_predict_match:
        parsed_data['eop_predict_end'] = parse_date(eop_predict_match.group(1))

    parsed_data['au_km'] = extract_float(r'1 au= ([\d.]+) km', data)
    parsed_data['c_km_s'] = extract_float(r'c= ([\d.]+) km/s', data)
    parsed_data['day_s'] = extract_float(r'1 day= ([\d.]+) s', data)

    cutoff_match = re.search(r'Elevation cut-off\s+:\s+([-\d.]+)', data)
    parsed_data['elevation_cutoff'] = float(cutoff_match.group(1)) if cutoff_match else None

    parsed_data['airmass_cutoff'] = extract_float(r'Airmass \(>(\d+\.\d+)=NO\)', data)
    
    solar_elongation_match = re.search(r'Solar elongation \(\s*([\d.]+),\s*([\d.]+)=NO', data)
    if solar_elongation_match:
        parsed_data['solar_elongation_cutoff_min'] = float(solar_elongation_match.group(1))
        parsed_data['solar_elongation_cutoff_max'] = float(solar_elongation_match.group(2))

    parsed_data['local_hour_angle_cutoff'] = extract_float(r'Local Hour Angle\( ([\d.]+)=NO', data)
    parsed_data['ra_dec_angular_rate_cutoff'] = extract_float(r'RA/DEC angular rate \(\s*([\d.]+)=NO', data)
    
    # parsed_data = {k: v for k, v in parsed_data.items() if v is not None}
    
    # New parsing logic for body classification
    parsed_data['body_type'] = determine_body_type(data, parsed_data)
    parsed_data['is_planet'] = parsed_data['body_type'] in ['terrestrial_planet', 'gas_giant']
    parsed_data['is_moon'] = parsed_data['body_type'] in ['major_moon', 'moon']
    
    # Parse parent body information
    parent_body_match = re.search(r'Target primary\s+:\s+(.+)', data)
    if parent_body_match:
        parsed_data['parent_body_name'] = parent_body_match.group(1).strip()
    else:
        parsed_data['parent_body_name'] = None

    # Parse additional fields for asteroid and comet classification
    parsed_data['absolute_magnitude'] = extract_float(r'Absolute mag\. H\s+=\s+([\d.]+)', data)
    parsed_data['albedo'] = parsed_data['geometric_albedo']  # We already parse this as geometric_albedo
    parsed_data['tisserand_parameter'] = extract_float(r'Tisserand\'s parameter\s+=\s+([\d.]+)', data)

    return parsed_data

def determine_body_type(data, parsed_data):
    name = parsed_data.get('name', '').lower() if parsed_data.get('name') else ''
    radius = parsed_data.get('vol_mean_radius')
    
    if not name and not data:
        return 'unknown'

    if 'sun' in name:
        return 'star'
    elif 'mercury' in name or 'venus' in name or 'earth' in name or 'mars' in name:
        return 'terrestrial_planet'
    elif 'jupiter' in name or 'saturn' in name or 'uranus' in name or 'neptune' in name:
        return 'gas_giant'
    elif 'pluto' in name or 'eris' in name or 'makemake' in name or 'haumea' in name:
        return 'dwarf_planet'
    elif radius and radius > 1000:  # Arbitrary threshold for major moons
        return 'major_moon'
    elif 'moon' in name or parsed_data.get('parent_body_name'):
        return 'moon'
    elif 'asteroid' in data.lower():
        if 'neo' in data.lower() or 'near-earth' in data.lower():
            return 'near_earth_asteroid'
        elif 'main belt' in data.lower():
            return 'main_belt_asteroid'
        elif 'trojan' in data.lower():
            return 'trojan_asteroid'
        else:
            return 'main_belt_asteroid'  # Default to main belt if not specified
    elif 'comet' in data.lower():
        if 'short-period' in data.lower():
            return 'short_period_comet'
        else:
            return 'long_period_comet'
    elif 'kuiper belt' in data.lower():
        return 'kuiper_belt_object'
    elif 'scattered disc' in data.lower():
        return 'scattered_disc_object'
    elif 'centaur' in data.lower():
        return 'centaur'
    else:
        return 'unknown'

def parse_date(date_string):
    date_string = date_string.replace("DATA-BASED ", "").strip()
    try:
        date = datetime.strptime(date_string, "%Y-%b-%d")
        return date.strftime("%Y-%m-%d")
    except ValueError:
        try:
            date = datetime.strptime(date_string, "%Y-%m-%d")
            return date.strftime("%Y-%m-%d")
        except ValueError:
            print(f"Unable to parse date: {date_string}")
            return None

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
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch oscillating elements for body ID {body_id}")
        return None

def parse_oscillating_elements(data):
    parsed_data = {}
    
    def extract_float(pattern, text):
        match = re.search(pattern, text)
        return float(match.group(1)) if match else None

    # Parse the initial osculating elements
    epoch_match = re.search(r'EPOCH=\s*([\d.]+)', data)
    parsed_data['epoch'] = float(epoch_match.group(1)) if epoch_match else None
    
    parsed_data['eccentricity'] = extract_float(r'EC=\s*([\d.]+)', data)
    parsed_data['perihelion_distance'] = extract_float(r'QR=\s*([\d.]+)', data)
    parsed_data['inclination'] = extract_float(r'IN=\s*([\d.]+)', data)
    parsed_data['longitude_of_ascending_node'] = extract_float(r'OM=\s*([\d.]+)', data)
    parsed_data['argument_of_perihelion'] = extract_float(r'W\s*=\s*([\d.]+)', data)
    parsed_data['time_of_perihelion_passage'] = extract_float(r'TP=\s*([\d.]+)', data)
    
    # Parse the first row of the ephemeris table for additional elements
    table_pattern = r'\$\$SOE(.*?)\$\$EOE'
    table_match = re.search(table_pattern, data, re.DOTALL)
    if table_match:
        table_data = table_match.group(1).strip().split('\n')[1]  # Get the first data row
        elements = table_data.split()
        if len(elements) >= 12:
            parsed_data['semi_major_axis'] = float(elements[9])
            parsed_data['aphelion_distance'] = float(elements[10])
            parsed_data['orbital_period'] = float(elements[11])
            parsed_data['mean_motion'] = float(elements[6])
    
    return parsed_data

def populate_celestial(start_id, end_id=None):
    if end_id is None:
        end_id = start_id
    
    for body_id in range(start_id, end_id + 1):
        update_celestial_body(body_id)

def update_celestial_body(body_id):
    print(f"Fetching data for body ID {body_id}")
    data = fetch_celestial_data(body_id)
    oscillating_data = fetch_oscillating_elements(body_id)
    
    if data and oscillating_data:
        parsed_data = parse_celestial_data(data)
        parsed_oscillating_data = parse_oscillating_elements(oscillating_data)
        
        # Merge the two parsed datasets
        parsed_data.update(parsed_oscillating_data)
        
        if parsed_data.get('name'):
            with transaction.atomic():
                try:
                    obj, created = CelestialBody.objects.update_or_create(
                        name=parsed_data['name'],
                        defaults=parsed_data
                    )
                    
                    # Handle parent body relationship
                    if parsed_data['parent_body_name']:
                        parent_body, _ = CelestialBody.objects.get_or_create(name=parsed_data['parent_body_name'])
                        obj.parent_body = parent_body
                        obj.save()
                    
                    if created:
                        print(f"Created new entry for {parsed_data['name']}")
                    else:
                        print(f"Updated existing entry for {parsed_data['name']}")
                except Exception as e:
                    print(f"Error creating/updating entry for {parsed_data['name']}: {str(e)}")
                    print("Parsed data:", parsed_data)
        else:
            print(f"No valid data found for body ID {body_id}")
    else:
        print(f"Failed to fetch data for body ID {body_id}")

def list_all_entries():
    entries = CelestialBody.objects.all().order_by('id')
    if entries:
        print("\nAll Celestial Bodies:")
        for entry in entries:
            print(f"ID: {entry.id}, Name: {entry.name}")
    else:
        print("No entries found in the database.")

def view_entry(identifier):
    try:
        if identifier.isdigit():
            body = CelestialBody.objects.get(id=int(identifier))
        else:
            body = CelestialBody.objects.get(name=identifier)
        
        print(f"\nDetails for {body.name} (ID: {body.id}):")
        for field in body._meta.fields:
            print(f"{field.name}: {getattr(body, field.name)}")
    except CelestialBody.DoesNotExist:
        print(f"No entry found for identifier: {identifier}")

def delete_entry(identifier):
    try:
        if identifier.isdigit():
            body = CelestialBody.objects.get(id=int(identifier))
        else:
            body = CelestialBody.objects.get(name=identifier)
        
        name = body.name
        body.delete()
        print(f"Deleted entry for {name}")
    except CelestialBody.DoesNotExist:
        print(f"No entry found for identifier: {identifier}")

def modify_entry(identifier, field, value):
    try:
        if identifier.isdigit():
            body = CelestialBody.objects.get(id=int(identifier))
        else:
            body = CelestialBody.objects.get(name=identifier)
        
        if hasattr(body, field):
            setattr(body, field, value)
            body.save()
            print(f"Updated {field} for {body.name} to {value}")
        else:
            print(f"Field {field} does not exist for CelestialBody")
    except CelestialBody.DoesNotExist:
        print(f"No entry found for identifier: {identifier}")

def manual_entry():
    print("\nManual Entry for Celestial Body")
    name = input("Enter the name of the celestial body: ")
    body_type = input("Enter the body type (e.g., terrestrial_planet, gas_giant, moon): ")
    
    # Get basic information
    vol_mean_radius = float(input("Enter the mean radius (km): "))
    mass = float(input("Enter the mass (10^24 kg): "))
    density = float(input("Enter the density (g/cm^3): "))
    
    # Get orbital information
    semi_major_axis = float(input("Enter the semi-major axis (AU): "))
    eccentricity = float(input("Enter the eccentricity: "))
    inclination = float(input("Enter the inclination (degrees): "))
    orbital_period = float(input("Enter the orbital period (Earth years): "))
    
    # Get rotational information
    sidereal_rot_period = float(input("Enter the sidereal rotation period (Earth days): "))
    
    # Create the celestial body entry
    try:
        with transaction.atomic():
            celestial_body = CelestialBody.objects.create(
                name=name,
                body_type=body_type,
                vol_mean_radius=vol_mean_radius,
                mass=mass,
                density=density,
                semi_major_axis=semi_major_axis,
                eccentricity=eccentricity,
                inclination=inclination,
                orbital_period=orbital_period,
                sidereal_rot_period=sidereal_rot_period
            )
        print(f"Successfully created entry for {name}")
    except Exception as e:
        print(f"Error creating entry: {str(e)}")

def main_menu():
    while True:
        print("\nCelestial Body Database Manager")
        print("1. Update database (range)")
        print("2. Update single celestial body")
        print("3. List all entries")
        print("4. View an entry")
        print("5. Delete an entry")
        print("6. Modify an entry")
        print("7. Manual entry of new celestial body")
        print("8. Exit")
        
        choice = input("Enter your choice (1-8): ")
        
        if choice == '1':
            start_id = int(input("Enter starting body ID: "))
            end_id = int(input("Enter ending body ID: "))
            populate_celestial(start_id, end_id)
        elif choice == '2':
            body_id = int(input("Enter the body ID to update: "))
            update_celestial_body(body_id)
        elif choice == '3':
            list_all_entries()
        elif choice == '4':
            identifier = input("Enter the ID number or name of the celestial body: ")
            view_entry(identifier)
        elif choice == '5':
            identifier = input("Enter the ID number or name of the celestial body to delete: ")
            confirm = input(f"Are you sure you want to delete this entry? (y/n): ")
            if confirm.lower() == 'y':
                delete_entry(identifier)
        elif choice == '6':
            identifier = input("Enter the ID number or name of the celestial body to modify: ")
            field = input("Enter the field name to modify: ")
            value = input("Enter the new value: ")
            modify_entry(identifier, field, value)
        elif choice == '7':
            manual_entry()
        elif choice == '8':
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main_menu()
