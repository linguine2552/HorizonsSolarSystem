from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CelestialBody
import hashlib
from django.conf import settings
import json
import random
import time
import math

def generate_binary_matrix():
    return [[random.randint(0, 1) for _ in range(15)] for _ in range(3)]

@csrf_exempt
def check_password(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        password = data.get('password')
        
        correct_password = getattr(settings, 'ACCESS_PASSWORD')
        
        if password == correct_password:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Incorrect password'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def get_password_hint(request):
    if request.method == 'GET':
        current_time = int(time.time())
        if current_time % 2 == 0:
            hint = generate_binary_matrix()
        else:
            hint = None
        
        return JsonResponse({'hint': hint})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@csrf_exempt
def verify_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded'})
        
        sha256_hash = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            sha256_hash.update(chunk)
        file_hash = sha256_hash.hexdigest()
        
        required_hash = getattr(settings, 'ACCESS_HASH', '')
        if file_hash.upper() == required_hash.upper():
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid file'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})    
    
def get_solar_system_data(request):
    if request.method == 'GET':
        bodies = CelestialBody.objects.all().values()
        solar_system_data = []

        for body in bodies:
            try:
                # Default radius to 1 if vol_mean_radius is None or not present
                radius = body.get('vol_mean_radius')
                if radius is None:
                    radius = body.get('target_radii_a') or body.get('target_radii_b') or body.get('target_radii_c') or 1
                radius = float(radius) / 1000  # Convert km to 1000 km units

                if body['body_type'] == 'star':  # Assuming the Sun is the only star
                    solar_system_data.append({
                        'name': body['name'],
                        'body_type': body['body_type'],
                        'radius': radius,
                        'x': 0,
                        'y': 0,
                        'z': 0
                    })
                else:
                    position = calculate_heliocentric_position(body)
                    if position:
                        X, Y, Z = position
                        solar_system_data.append({
                            'name': body['name'],
                            'body_type': body['body_type'],
                            'radius': radius,
                            'x': X,
                            'y': Y,
                            'z': Z
                        })
                    else:
                        print(f"Skipping {body['name']} due to insufficient orbital data")
            except Exception as e:
                print(f"Error processing {body.get('name', 'Unknown body')}: {str(e)}")
                continue  # Skip this body and continue with the next one

        return JsonResponse(solar_system_data, safe=False)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def calculate_heliocentric_position(body):
    try:
        # Check if all required orbital elements are present
        required_elements = ['semi_major_axis', 'eccentricity', 'inclination', 'mean_longitude', 
                             'longitude_of_periapsis', 'longitude_of_ascending_node']
        
        if any(body.get(element) is None for element in required_elements):
            return None  # Return None if any required element is missing

        # Convert degrees to radians
        a = float(body['semi_major_axis'])  # in AU
        e = float(body['eccentricity'])
        i = math.radians(float(body['inclination']))
        L = math.radians(float(body['mean_longitude']))
        long_peri = math.radians(float(body['longitude_of_periapsis']))
        long_node = math.radians(float(body['longitude_of_ascending_node']))

        # Calculate mean anomaly
        M = L - long_peri

        # Solve Kepler's equation (simplified approach)
        E = M
        for _ in range(5):  # Iterate a few times for better accuracy
            E = M + e * math.sin(E)

        # Calculate true anomaly
        v = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E/2), math.sqrt(1 - e) * math.cos(E/2))

        # Calculate distance from Sun
        r = a * (1 - e * math.cos(E))

        # Calculate heliocentric position in AU
        X = (math.cos(long_node) * math.cos(v + long_peri - long_node) - 
             math.sin(long_node) * math.sin(v + long_peri - long_node) * math.cos(i)) * r
        Y = (math.sin(long_node) * math.cos(v + long_peri - long_node) + 
             math.cos(long_node) * math.sin(v + long_peri - long_node) * math.cos(i)) * r
        Z = math.sin(v + long_peri - long_node) * math.sin(i) * r

        return X, Y, Z
    except Exception as e:
        print(f"Error calculating position for {body.get('name', 'Unknown body')}: {str(e)}")
        return None