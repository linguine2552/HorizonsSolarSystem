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

def parse_jpl_horizons_object(data):
    parsed_data = {}
    
    # Extract name
    name_patterns = [
        r'Revised:.*?\s+(\w+)\s+\d+,\s+\d+\s+(.*?)\s+(\d+)',
        r'Target body name:\s*(.*?)\s*\(.*?\)',
        r'Horizons> Designation: (.*)'  # Add this pattern
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, data, re.IGNORECASE | re.MULTILINE)
        if name_match:
            if 'Target body name:' in pattern:
                parsed_data['name'] = name_match.group(1).strip()
            elif 'Horizons>' in pattern:
                parsed_data['name'] = name_match.group(1).strip()
            else:
                parsed_data['name'] = name_match.group(2).strip()
            break
    
    if 'name' not in parsed_data:
        print("Error: Unable to extract name")

    # Physical characteristics
    characteristics = [
        ('name', [
            r'Revised:.*?\s+(\w+)\s+\d+,\s+\d+\s+(.*?)\s+(\d+)',
            r'Target body name:\s*(.*?)\s*\(.*?\)'
        ]),
        ('vol_mean_radius', [
            r'(?:Vol\.\s*Mean\s*Radius|Vol\.\s*mean\s*radius)\s*\(km\)\s*=\s*([\d.]+)(?:\+-\s*([\d.]+))?',
            r'Vol\.\s*Mean\s*Radius\s*\(km\)\s*=\s*([\d.]+)(?:\+-\s*([\d.]+))?',
            r'Target radii\s*:\s*([\d.]+)\s*km'
        ]),
        ('density', [
            r'Density\s*\(g\/cm\^3\)\s*=\s*([\d.]+)\((\d+)\+-(\d+)\)',
            r'Density,\s*g\/cm\^3\s*=\s*([\d.]+)',
            r'Density\s*\(g\s*cm\^-3\)\s*=\s*([\d.]+)'
        ]),
        ('mass', [
            r'Mass\s*(?:x10\^(\d+))?\s*\(kg\)\s*=\s*([\d.]+)(?:\+-\s*([\d.]+))?',
            r'GM=\s*([\d.]+)'
        ]),
        ('flattening', [
            r'(?:Flattening|flattening)(?:,\s*f)?\s*=\s*(?:1\/)?([\d.]+)',
            r'Mom\.\s*of\s*Inertia\s*=\s*([\d.]+)'
        ]),
        ('volume', [
            r'Volume(?:,\s*km\^3|(?:\s*\(x10\^(?:\d+)\s*km\^3\)))\s*=\s*([\d.]+)(?:\s*x\s*10\^(\d+))?'
        ]),
        ('equatorial_radius', [
            r'Equatorial\s*radius\s*\(km\)\s*=\s*([\d.]+)',
            r'Equ\.\s*radius,\s*km\s*=\s*([\d.]+)',
            r'Equatorial\s*radius,\s*Re\s*=\s*([\d.]+)\s*km',
            r'Target radii\s*:\s*([\d.]+)\s*km'
        ]),
        ('sidereal_rot_period', [
            r'Sidereal\s*rot\.\s*period\s*=\s*([\d.]+)\s*(?:d|hr)',
            r'Mean\s*sidereal\s*day,\s*hr\s*=\s*([\d.]+)',
            r'ROTPER=\s*([\d.]+)'
        ]),
        ('sid_rot_rate', [
            r'Sid\.\s*rot\.\s*rate,\s*rad\/s\s*=\s*([\d.E+-]+)',
            r'Rot\.\s*Rate\s*\(rad\/s\)\s*=\s*([\d.E+-]+)',
            r'Sid\.\s*rot\.\s*rate\s*\(rad\/s\)\s*=\s*([\d.E+-]+)'
        ]),
        ('mean_solar_day', [
            r'Mean\s*solar\s*day\s*\(sol\)\s*=\s*([\d.]+)\s*s',
            r'Mean\s*solar\s*day\s*(?:\d+\.0)?,\s*s\s*=\s*([\d.]+)',
            r'Mean\s*solar\s*day\s*=\s*([\d.]+)\s*d'
        ]),
        ('polar_gravity', [
            r'Polar\s*gravity\s*m\/s\^2\s*=\s*([\d.]+)',
            r'g_p,\s*m\/s\^2\s*\(polar\)\s*=\s*([\d.]+)',
            r'Equ\.\s*gravity\s*m\/s\^2\s*=\s*([\d.]+)'
        ]),
        ('core_radius', [
            r'(?:Fluid\s*)?[Cc]ore\s*rad(?:ius)?\s*(?:\(km\))?\s*=\s*(?:~)?([\d.]+)'
        ]),
        ('equatorial_gravity', [
            r'Equ\.\s*gravity\s*m\/s\^2\s*=\s*([\d.]+)',
            r'g_e,\s*m\/s\^2\s*\(equatorial\)\s*=\s*([\d.]+)'
        ]),
        ('geometric_albedo', [
            r'Geometric\s*[Aa]lbedo\s*=\s*([\d.]+)',
            r'ALBEDO=\s*([\d.]+)'
        ])
    ]

    # Apply the updated patterns with fallbacks
    for char, patterns in characteristics:
        value = None
        for pattern in patterns:
            match = re.search(pattern, data, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                if char == 'name':
                    value = match.group(1).strip() if char == 'name' and 'Target body name:' in pattern else match.group(2).strip()
                elif char == 'mass':
                    if 'GM=' in pattern:
                        # Convert GM to mass (assuming G = 6.67430 x 10^-11 m^3 kg^-1 s^-2)
                        gm = float(match.group(1))
                        value = gm / (6.67430e-11)
                    elif match.group(1):  # If exponent is present
                        exponent = int(match.group(1))
                        mantissa = float(match.group(2))
                        value = mantissa * (10 ** (exponent - 24))  # Convert to 10^24 kg
                        if match.group(3):
                            parsed_data[f'{char}_uncertainty'] = float(match.group(3)) * (10 ** (exponent - 24))
                    else:  # If mass is given directly
                        value = float(match.group(2))
                        if match.group(3):
                            parsed_data[f'{char}_uncertainty'] = float(match.group(3))
                elif char == 'volume':
                    mantissa = float(match.group(1))
                    if match.group(2):  # If exponent is present
                        exponent = int(match.group(2))
                        value = mantissa * (10 ** (exponent - 10))  # Convert to 10^10 km^3
                    else:
                        value = mantissa
                elif char == 'flattening':
                    if 'Mom. of Inertia' in pattern:
                        moment_of_inertia = float(match.group(1))
                        value = 1 - (5/2) * (1 - moment_of_inertia / 0.4)  # Assuming a perfect sphere has I = 0.4MR^2
                    else:
                        flattening = float(match.group(1))
                        value = 1 / flattening if flattening > 1 else flattening
                elif char in ['sidereal_rot_period', 'mean_solar_day']:
                    value = float(match.group(1))
                    if 'd' in match.group(0).lower():
                        value *= 24  # Convert days to hours
                    elif 's' in match.group(0).lower():
                        value /= 3600  # Convert seconds to hours
                elif char == 'density' and len(match.groups()) > 2:
                    value = float(match.group(1))
                    uncertainty = float(match.group(2)) * 10**-int(match.group(3))
                    parsed_data[f'{char}_uncertainty'] = uncertainty
                else:
                    value = float(match.group(1))
                    if len(match.groups()) > 1 and match.group(2):
                        parsed_data[f'{char}_uncertainty'] = float(match.group(2))
                break  # Stop trying patterns if we found a match

        if value is not None:
            parsed_data[char] = value
        else:
            print(f"Warning: Unable to extract {char}")

    # Gravitational characteristics
    gm_match = re.search(r'GM[,\s]*\(?km\^3\/s\^2\)?\s*=\s*([\d.]+)', data, re.IGNORECASE)
    if gm_match:
        parsed_data['gm'] = float(gm_match.group(1))

    gm_uncertainty_match = re.search(r'GM 1-sigma[,\s]*\(?km\^3\/s\^2\)?\s*=\s*([\d.]+)', data, re.IGNORECASE)
    if gm_uncertainty_match:
        parsed_data['gm_uncertainty'] = float(gm_uncertainty_match.group(1))

    mass_ratio_match = re.search(r'Mass ratio[,\s]*\((?:Sun|Earth)\/(?:planet|Earth)\)\s*=\s*([\d.]+)', data, re.IGNORECASE)
    if mass_ratio_match:
        parsed_data['mass_ratio'] = float(mass_ratio_match.group(1))

    # Atmospheric characteristics
    atmos_mass_match = re.search(r'Mass of atmosphere[,\s]*kg\s*=\s*(?:~\s*)?([\d.]+)\s*x\s*10\^(\d+)', data, re.IGNORECASE)
    if atmos_mass_match:
        mantissa = float(atmos_mass_match.group(1))
        exponent = int(atmos_mass_match.group(2))
        parsed_data['atmosphere_mass'] = mantissa * (10 ** exponent)

    mean_temp_match = re.search(r'Mean (?:surface )?temp(?:erature)?[,\s]*\(?K\)?\s*=\s*([\d.]+)', data, re.IGNORECASE)
    if mean_temp_match:
        parsed_data['mean_temperature'] = float(mean_temp_match.group(1))
    else:
        # Try alternative format
        alt_mean_temp_match = re.search(r'Mean surface temp.*?:\s*([\d.]+)', data)
        if alt_mean_temp_match:
            parsed_data['mean_temperature'] = float(alt_mean_temp_match.group(1))

    surface_pressure_match = re.search(r'Atm(?:os)?\.? pressure\s*=\s*([\d.]+)\s*(?:bar|atm)', data, re.IGNORECASE)
    if surface_pressure_match:
        parsed_data['surface_pressure'] = float(surface_pressure_match.group(1))

    # Orbital characteristics
    obliquity_match = re.search(r'Obliquity to (?:orbit|ecliptic)[,\s]*(?:deg)?\s*=\s*([\d.]+)', data, re.IGNORECASE)
    if obliquity_match:
        parsed_data['obliquity_to_orbit'] = float(obliquity_match.group(1))

    sidereal_period_match = re.search(r'(?:Mean )?[Ss]idereal (?:orb(?:it)?)? period\s*=\s*([\d.]+)\s*([yd])', data, re.IGNORECASE)
    if sidereal_period_match:
        value = float(sidereal_period_match.group(1))
        unit = sidereal_period_match.group(2)
        if unit.lower() == 'y':
            parsed_data['mean_sidereal_orbit_period_years'] = value
            parsed_data['mean_sidereal_orbit_period_days'] = value * 365.25
        elif unit.lower() == 'd':
            parsed_data['mean_sidereal_orbit_period_days'] = value
            parsed_data['mean_sidereal_orbit_period_years'] = value / 365.25

    visual_magnitude_match = re.search(r'Visual mag(?:nitude)?\.? V\(1,0\)\s*=\s*([-\d.]+)', data, re.IGNORECASE)
    if visual_magnitude_match:
        parsed_data['visual_magnitude'] = float(visual_magnitude_match.group(1))

    orbital_speed_match = re.search(r'Orbital speed[,\s]*km\/s\s*=\s*([\d.]+)', data, re.IGNORECASE)
    if orbital_speed_match:
        parsed_data['orbital_speed'] = float(orbital_speed_match.group(1))

    hill_sphere_match = re.search(r"Hill's sphere rad(?:ius)?\.? Rp\s*=\s*([\d.]+)", data, re.IGNORECASE)
    if hill_sphere_match:
        parsed_data['hill_sphere_radius'] = float(hill_sphere_match.group(1))

    escape_speed_match = re.search(r'Escape (?:velocity|speed)[,\s]*km\/s\s*=\s*([\d.]+)', data, re.IGNORECASE)
    if escape_speed_match:
        parsed_data['escape_speed'] = float(escape_speed_match.group(1))

    # Calculate maximum angular diameter
    equatorial_radius_match = re.search(r'Equ\. radius, km\s+=\s+([\d.]+)', data)
    if equatorial_radius_match:
        equatorial_radius = float(equatorial_radius_match.group(1))
        
        # For outer solar system objects
        perihelion_match = re.search(r'Perihelion, a.u.\s+=\s+([\d.]+)', data)
        if perihelion_match:
            perihelion = float(perihelion_match.group(1))
            earth_aphelion = 1.01671388  # Earth's aphelion in AU
            closest_approach = perihelion - earth_aphelion
        else:
            # For inner solar system objects
            aphelion_match = re.search(r'Aphelion, a.u.\s+=\s+([\d.]+)', data)
            if aphelion_match:
                aphelion = float(aphelion_match.group(1))
                earth_perihelion = 0.98329134  # Earth's perihelion in AU
                closest_approach = earth_perihelion - aphelion
            else:
                closest_approach = None

        if closest_approach:
            # Convert AU to km
            closest_approach_km = closest_approach * 149597870.7  # 1 AU in km
            
            # Calculate maximum angular diameter in arcseconds
            max_angular_diameter = 2 * math.atan(equatorial_radius / closest_approach_km) * (180 / math.pi) * 3600
            parsed_data['max_angular_diameter'] = max_angular_diameter

    # Solar interaction
    solar_constant_match = re.search(r'Solar Constant \(W\/m\^2\)\s*(?:=|:)\s*([\d.]+)\s*(?:\(mean\))?,?\s*([\d.]+)\s*\(?(?:peri|min)\)?,?\s*([\d.]+)\s*\(?(?:aph|max)\)?', data, re.IGNORECASE)
    if solar_constant_match:
        parsed_data['solar_constant_mean'] = float(solar_constant_match.group(1))
        parsed_data['solar_constant_perihelion'] = float(solar_constant_match.group(2))
        parsed_data['solar_constant_aphelion'] = float(solar_constant_match.group(3))

    # The JPL Horizons data doesn't directly provide Planetary IR values
    # We can estimate these based on the solar constant and albedo
    if 'solar_constant_mean' in parsed_data and 'geometric_albedo' in parsed_data:
        albedo = parsed_data['geometric_albedo']
        
        # Estimate mean maximum planetary IR
        absorbed_solar_energy = parsed_data['solar_constant_mean'] * (1 - albedo)
        parsed_data['max_planetary_ir_mean'] = absorbed_solar_energy / 4  # Divide by 4 for day/night and spherical distribution

        # Estimate perihelion and aphelion maximum planetary IR
        if 'solar_constant_perihelion' in parsed_data:
            absorbed_solar_energy_perihelion = parsed_data['solar_constant_perihelion'] * (1 - albedo)
            parsed_data['max_planetary_ir_perihelion'] = absorbed_solar_energy_perihelion / 4

        if 'solar_constant_aphelion' in parsed_data:
            absorbed_solar_energy_aphelion = parsed_data['solar_constant_aphelion'] * (1 - albedo)
            parsed_data['max_planetary_ir_aphelion'] = absorbed_solar_energy_aphelion / 4

        # Estimate minimum planetary IR (night-side emission)
        # This is a very rough estimate and might not be accurate for all bodies
        parsed_data['min_planetary_ir'] = parsed_data['max_planetary_ir_mean'] * 0.1  # Assume night-side emits about 10% of day-side

    # Osculating orbital elements and additional derived elements
    orbital_elements = re.findall(r'(\d{7}\.\d+)\s*=.*?\n\s*EC=\s*([\d.E+-]+)\s*QR=\s*([\d.E+-]+)\s*IN=\s*([\d.E+-]+)\s*\n\s*OM=\s*([\d.E+-]+)\s*W\s*=\s*([\d.E+-]+)\s*Tp=\s*([\d.E+-]+)\s*\n\s*N\s*=\s*([\d.E+-]+)\s*MA=\s*([\d.E+-]+)\s*TA=\s*([\d.E+-]+)\s*\n\s*A\s*=\s*([\d.E+-]+)\s*AD=\s*([\d.E+-]+)\s*PR=\s*([\d.E+-]+)', data)

    if orbital_elements:
        # Use the first set of orbital elements (you might want to modify this if you need multiple epochs)
        elements = orbital_elements[0]
        parsed_data['epoch'] = float(elements[0])
        parsed_data['eccentricity'] = float(elements[1])
        parsed_data['inclination'] = float(elements[3])
        parsed_data['longitude_of_ascending_node'] = float(elements[4])
        parsed_data['argument_of_perihelion'] = float(elements[5])  # This is the same as argument_of_periapsis
        parsed_data['semi_major_axis'] = float(elements[10])
        
        # Additional derived elements
        parsed_data['perihelion_distance'] = float(elements[2])
        parsed_data['aphelion_distance'] = float(elements[11])
        parsed_data['orbital_period'] = float(elements[12]) / 365.25  # Convert days to years
        parsed_data['mean_motion'] = float(elements[7])
        parsed_data['time_of_perihelion_passage'] = float(elements[6])
        
        # Calculate mean longitude
        mean_anomaly = float(elements[8])
        longitude_of_periapsis = parsed_data['longitude_of_ascending_node'] + parsed_data['argument_of_perihelion']
        parsed_data['mean_longitude'] = (mean_anomaly + longitude_of_periapsis) % 360
        
        # Calculate longitude of periapsis
        parsed_data['longitude_of_periapsis'] = longitude_of_periapsis % 360

    return parsed_data

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

    parsed_data = parse_jpl_horizons_object(data)
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
        parsed_data = parse_jpl_horizons_object(combined_data)
        
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