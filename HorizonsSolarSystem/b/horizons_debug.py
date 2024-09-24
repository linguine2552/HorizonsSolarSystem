import os
import django
import requests
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "b.settings")
django.setup()

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
    
    # Helper function to extract float values
    def extract_float(pattern, text):
        match = re.search(pattern, text)
        return float(match.group(1)) if match else None

    # Extract name
    name_match = re.search(r'Target body name: (.+?) \(', data)
    parsed_data['name'] = name_match.group(1) if name_match else None

    # Extract physical data
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

    parsed_data['gm'] = extract_float(r'GM \(km\^3/s\^2\)\s+=\s+([\d.]+)', data)
    parsed_data['gm_uncertainty'] = extract_float(r'GM 1-sigma \(km\^3/s\^2\) = \+- ([\d.]+)', data)
    parsed_data['mass_ratio_to_sun'] = extract_float(r'Mass ratio \(Sun/Mars\) = ([\d.]+)', data)
    
    parsed_data['atmosphere_mass'] = extract_float(r'Mass of atmosphere, kg= ~ ([\d.]+) x 10\^(\d+)', data)
    parsed_data['mean_temperature'] = extract_float(r'Mean temperature \(K\)\s+=\s+([\d.]+)', data)
    parsed_data['surface_pressure'] = extract_float(r'Atmos\. pressure \(bar\)\s+=\s+([\d.]+)', data)

    parsed_data['obliquity_to_orbit'] = extract_float(r'Obliquity to orbit\s+=\s+([\d.]+)', data)
    parsed_data['max_angular_diameter'] = extract_float(r'Max\. angular diam\.\s+=\s+([\d.]+)', data)
    parsed_data['mean_sidereal_orbit_period_years'] = extract_float(r'Mean sidereal orb per =\s+([\d.]+)', data)
    parsed_data['mean_sidereal_orbit_period_days'] = extract_float(r'Mean sidereal orb per =\s+[\d.]+ y\s+([\d.]+)', data)
    parsed_data['visual_magnitude'] = extract_float(r'Visual mag\. V\(1,0\)\s+=\s+([-\d.]+)', data)
    parsed_data['orbital_speed'] = extract_float(r'Orbital speed,\s+km/s\s+=\s+([\d.]+)', data)
    parsed_data['hill_sphere_radius'] = extract_float(r'Hill\'s sphere rad\. Rp =\s+([\d.]+)', data)
    parsed_data['escape_speed'] = extract_float(r'Escape speed, km/s\s+=\s+([\d.]+)', data)

    # Extract solar interaction data
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

    # Extract additional tertiary information
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

    eop_coverage_match = re.search(r'EOP coverage\s+: (.+) TO (.+)', data)
    if eop_coverage_match:
        parsed_data['eop_coverage_start'] = eop_coverage_match.group(1)
        parsed_data['eop_coverage_end'] = eop_coverage_match.group(2)

    parsed_data['eop_predict_end'] = re.search(r'EOP PREDICTS-> (.+)', data).group(1) if re.search(r'EOP PREDICTS-> (.+)', data) else None

    parsed_data['au_km'] = extract_float(r'1 AU= ([\d.]+) km', data)
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
    
    return parsed_data

def print_parsed_data(parsed_data):
    print("\nParsed Celestial Body Data:")
    print("=" * 30)
    for key, value in parsed_data.items():
        print(f"{key}: {value}")

def main():
    body_id = 499  # Mars
    print(f"Fetching data for body ID {body_id} (Mars)")
    data = fetch_celestial_data(body_id)
    if data:
        parsed_data = parse_celestial_data(data)
        print_parsed_data(parsed_data)
    else:
        print("Failed to fetch data")

if __name__ == '__main__':
    main()