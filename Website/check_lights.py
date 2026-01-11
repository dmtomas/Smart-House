#!/usr/bin/env python3
import requests

API_URL = "http://192.168.1.143:5000/api/lights"

# Get all lights
def get_all_lights():
    response = requests.get(API_URL)
    if response.ok:
        data = response.json()
        return data['lights']
    return {}

# Get specific light
def get_light(light_id):
    response = requests.get(f"{API_URL}/{light_id}")
    if response.ok:
        data = response.json()
        return data['light']
    return None

# Turn light ON
def turn_on(light_id):
    response = requests.post(
        f"{API_URL}/{light_id}/toggle",
        json={'state': True}
    )
    return response.ok

# Turn light OFF
def turn_off(light_id):
    response = requests.post(
        f"{API_URL}/{light_id}/toggle",
        json={'state': False}
    )
    return response.ok

# Check if light is on
def is_light_on(light_id):
    light = get_light(light_id)
    if light:
        return light.get('state', False)
    return False

# Example usage
if __name__ == '__main__':
    # Get all lights
    lights = get_all_lights()
    print("All lights:", lights)

    # Check specific light
    if is_light_on('living'):
        print("Living room light is ON")
    else:
        print("Living room light is OFF")

    # Turn on living room
    turn_on('living')
    print("Turned on living room light")

    # Turn off kitchen
    turn_off('kitchen')
    print("Turned off kitchen light")
