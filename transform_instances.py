#!/usr/bin/env python
"""
Transform Cordeau's MDVRPTW instances into MDHF-VRPTW-SPD (vehicle routing problem with time windows,simultaneous pickups and deliveries, multiple depots and heterogeneous fleet.) instances in JSON format.
http://neo.lcc.uma.es/vrp/vrp-instances/multiple-depot-vrp-instances/
This provides a structured representation with explicit vehicle type organization.
Author: ANASS TAHA
Date: May 15, 2025
"""

import os
import random
import math
import json
from datetime import datetime

# Set fixed random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Configuration parameters
PICKUP_HANDLING_FACTOR = 0.5  # Additional service time per returned item (in minutes)

# Base operation time (for positioning and paperwork)
BASE_OPERATION_TIME_FACTOR = 0.2  # Factor of original service time for base operations, min 1 minute

# Customer categories distribution
CATEGORY_A_THRESHOLD = 0.70  # Delivery + low return if u_i < 0.70
CATEGORY_B_THRESHOLD = 0.90  # Delivery + significant return if 0.70 <= u_i < 0.90
                           # Category C (return-only) if u_i >= 0.90

# Pickup quantity factors
CATEGORY_A_PICKUP_MIN = 0.05
CATEGORY_A_PICKUP_MAX = 0.20
CATEGORY_B_PICKUP_MIN = 0.20 
CATEGORY_B_PICKUP_MAX = 0.50

# Vehicle classes (relative to original capacity Q*)
VEHICLE_CLASSES = [
    {"name": "Class1", "type": "Cargo bike/micro-EV", "capacity_factor": 0.25, 
     "fixed_cost": 60, "variable_cost": 0.45},
    {"name": "Class2", "type": "Small van (1 t)", "capacity_factor": 0.50, 
     "fixed_cost": 120, "variable_cost": 0.60},
    {"name": "Class3", "type": "Large van (2 t)", "capacity_factor": 0.80, 
     "fixed_cost": 180, "variable_cost": 0.75},
    {"name": "Class4", "type": "7.5-t truck", "capacity_factor": 1.20, 
     "fixed_cost": 240, "variable_cost": 0.90}
]

def transform_instance_to_json(input_file, output_file):
    """Transform a single MDVRPTW instance into MDHF-VRPTW-SPD in JSON format"""
    print(f"Transforming {input_file} to {output_file}")
    
    # Extract base filename for metadata
    base_filename = os.path.basename(input_file)
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Parse the first line
    first_line = lines[0].split()
    vrp_type = int(first_line[0])
    num_vehicles = int(first_line[1])
    num_customers = int(first_line[2])
    num_depots = int(first_line[3])
    
    # Different handling based on problem type
    has_time_windows = (vrp_type == 6)  # Type 6 = MDVRPTW, Type 2 = MDVRP
    if not has_time_windows:
        print(f"Instance {base_filename} is type {vrp_type}, not type 6 (MDVRPTW). Creating artificial time windows.")
    
    # Extract depot information
    depot_info = []
    for i in range(1, num_depots + 1):
        depot_line = lines[i].split()
        duration = int(depot_line[0])
        capacity = int(depot_line[1])
        depot_info.append((duration, capacity))
    
    # Extract customer information with format awareness - following the CordeauMDVRPTWReader pattern
    customers = []
    for i in range(num_depots + 1, num_depots + num_customers + 1):
        if i >= len(lines):
            raise ValueError(f"Line {i} doesn't exist in the file (total lines: {len(lines)})")
            
        line = lines[i].strip()
        # Split by multiple spaces to handle variable whitespace
        tokens = line.split()
        
        if len(tokens) < 5:  # Need at least ID, x, y, service time, demand
            raise ValueError(f"Line {i} has insufficient data: {line}")
        
        try:
            # Always extract the basic fields (ID, coordinates, service time, demand)
            customer_id = int(tokens[0])
            x = float(tokens[1])
            y = float(tokens[2])
            service_time = float(tokens[3])
            demand = int(tokens[4])
            
            # For MDVRPTW (type 6), time windows are at the end
            if has_time_windows:
                # Time windows are at positions n-2 and n-1 in MDVRPTW format
                # This is more robust than assuming fixed positions
                time_window_start = int(tokens[-2])
                time_window_end = int(tokens[-1])
            else:
                # Create default time windows for MDVRP
                max_duration = max(depot[0] for depot in depot_info)
                time_window_start = 0
                time_window_end = max_duration if max_duration > 0 else 1000
        
        except (IndexError, ValueError) as e:
            print(f"Error parsing line {i}: {line}")
            print(f"Tokens: {tokens}")
            raise ValueError(f"Format error in line {i}: {str(e)}")
        
        customers.append({
            'id': customer_id,
            'x': x,
            'y': y,
            'service_time': service_time,
            'demand': demand,
            'tw_start': time_window_start,
            'tw_end': time_window_end
        })
    
    # Extract depot coordinates
    depot_coords = []
    for i in range(num_depots + num_customers + 1, num_depots + num_customers + num_depots + 1):
        if i < len(lines):
            depot_line = lines[i].split()
            depot_id = int(depot_line[0])
            x = float(depot_line[1])
            y = float(depot_line[2])
            depot_coords.append((depot_id, x, y))
        else:
            print(f"Warning: Missing depot coordinates for depot at expected line {i}")
    
    # Apply the transformation steps from the guide
    
    # 1. Base data is already extracted above
    
    # 2. Split customers into demand categories
    for customer in customers:
        # Generate a random value for categorization
        u_i = random.random()
        
        if u_i < CATEGORY_A_THRESHOLD:
            customer['category'] = 'A'  # Delivery + low return
        elif u_i < CATEGORY_B_THRESHOLD:
            customer['category'] = 'B'  # Delivery + significant return
        else:
            customer['category'] = 'C'  # Return-only
    
    # 3. Generate pickup and delivery quantities
    smallest_vehicle_capacity = min(depot_info, key=lambda x: x[1])[1] * VEHICLE_CLASSES[0]['capacity_factor']
    
    for customer in customers:
        if customer['category'] == 'A':
            # Keep original delivery, low pickup
            delivery_qty = customer['demand']
            pickup_factor = CATEGORY_A_PICKUP_MIN + random.random() * (CATEGORY_A_PICKUP_MAX - CATEGORY_A_PICKUP_MIN)
            pickup_qty = math.ceil(pickup_factor * delivery_qty)
        
        elif customer['category'] == 'B':
            # Keep original delivery, significant pickup
            delivery_qty = customer['demand']
            pickup_factor = CATEGORY_B_PICKUP_MIN + random.random() * (CATEGORY_B_PICKUP_MAX - CATEGORY_B_PICKUP_MIN)
            pickup_qty = math.ceil(pickup_factor * delivery_qty)
        
        else:  # Category C
            # Zero delivery, small pickup (1-3 units as specified in guide)
            delivery_qty = 0
            # Calculate average delivery to set a reasonable pickup amount
            avg_delivery = sum(c['demand'] for c in customers) / len(customers)
            # Keep pickups between 1-3 as mentioned in the guide
            pickup_qty = random.randint(1, min(3, max(1, math.ceil(avg_delivery * 0.15))))
        
        # Ensure combined demand doesn't exceed smallest vehicle capacity
        if delivery_qty + pickup_qty > smallest_vehicle_capacity:
            # Scale down pickup quantity
            pickup_qty = max(1, int(smallest_vehicle_capacity - delivery_qty))
        
        customer['delivery_qty'] = delivery_qty
        customer['pickup_qty'] = pickup_qty
    
    # 5. Adjust service times for pickups
    for customer in customers:
        original_service_time = customer['service_time']
        delivery_qty = customer['delivery_qty']
        pickup_qty = customer['pickup_qty']
        
        # Base time for vehicle positioning and paperwork (applied to both operations when needed)
        base_time = max(min(original_service_time * BASE_OPERATION_TIME_FACTOR, 1.0), 0.5)
        
        # For customers with both pickup and delivery
        if delivery_qty > 0 and pickup_qty > 0:
            # Split service time proportionally, each operation has its own base time
            total_qty = delivery_qty + pickup_qty
            
            # Calculate proportional service times based on quantity ratio
            delivery_service_time = base_time + (original_service_time - 2*base_time) * (delivery_qty / total_qty)
            pickup_service_time = base_time + (original_service_time - 2*base_time) * (pickup_qty / total_qty)
            
            # Add handling time for pickup operations
            pickup_service_time += (PICKUP_HANDLING_FACTOR * pickup_qty)
            
        # For delivery-only customers
        elif delivery_qty > 0:
            delivery_service_time = original_service_time
            pickup_service_time = 0
            
        # For pickup-only customers (Category C)
        else:
            delivery_service_time = 0
            pickup_service_time = original_service_time + (PICKUP_HANDLING_FACTOR * pickup_qty)
        
        # Store the calculated service times
        customer['delivery_service_time'] = round(delivery_service_time, 1)
        customer['pickup_service_time'] = round(pickup_service_time, 1)
        
        # Calculate total service time
        total_service_time = delivery_service_time + pickup_service_time
        customer['new_service_time'] = round(total_service_time, 1)
        
        # Check if time window needs adjustment based on the total service time
        if customer['tw_start'] + total_service_time > customer['tw_end']:
            # Shift the end of time window forward just enough
            customer['tw_end'] = math.ceil(customer['tw_start'] + total_service_time)
    
    # Create statistics
    category_counts = {'A': 0, 'B': 0, 'C': 0}
    total_delivery = 0
    total_pickup = 0
    
    for customer in customers:
        category_counts[customer['category']] += 1
        total_delivery += customer['delivery_qty']
        total_pickup += customer['pickup_qty']
    
    # Create the JSON structure
    instance = {
        "metadata": {
            "instanceName": f"taha{base_filename.replace('pr', '')}-n{num_customers}",
            "randomSeed": RANDOM_SEED,
            "customerCount": num_customers,
            "depotCount": num_depots,
            "statistics": {
                "nb_DeliveryWithLowReturn": category_counts['A'],
                "nb_DeliveryWithSignificantReturn": category_counts['B'],
                "nb_ReturnOnly": category_counts['C'],
                "totalDeliveryQuantity": total_delivery,
                "totalPickupQuantity": total_pickup,
                "pickupToDeliveryRatio": round(total_pickup / total_delivery * 100, 1) if total_delivery > 0 else "N/A"
            }
        },
        "vehicleTypes": [],
        "depots": [],
        "customers": []
    }
    
    # Add vehicle type definitions
    for i, vehicle_class in enumerate(VEHICLE_CLASSES):
        instance["vehicleTypes"].append({
            "id": f"Type{i+1}",
            "name": vehicle_class["name"],
            "description": vehicle_class["type"],
            "capacityFactor": vehicle_class["capacity_factor"],
            "fixedCost": vehicle_class["fixed_cost"],
            "variableCost": vehicle_class["variable_cost"]
        })
    
    # Add depot information with unlimited vehicle availability
    for i, (depot_id, x, y) in enumerate(depot_coords):
        if i < len(depot_info):  # Make sure we have matching depot info
            duration = depot_info[i][0]
            base_capacity = depot_info[i][1]
            
            depot = {
                "id": depot_id,
                "x": x,
                "y": y,
                "maxDuration": duration,
                "vehicles": []
            }
            
            # Add unlimited vehicles of each type
            for j, vehicle_class in enumerate(VEHICLE_CLASSES):
                capacity = math.floor(base_capacity * vehicle_class["capacity_factor"])
                depot["vehicles"].append({
                    "typeId": f"Type{j+1}",
                    "capacity": capacity,
                    "count": "unlimited",  # Infinite units of each type
                    "maxDuration": duration
                })
            
            instance["depots"].append(depot)
    
    # Add customer information
    for customer in customers:
        instance["customers"].append({
            "id": customer["id"],
            "x": customer["x"],
            "y": customer["y"],
            "TotalServiceTime": customer["new_service_time"],
            "deliveryServiceTime": customer["delivery_service_time"],
            "pickupServiceTime": customer["pickup_service_time"],
            "deliveryQuantity": customer["delivery_qty"],
            "pickupQuantity": customer["pickup_qty"],
            "category": customer["category"],
            "timeWindow": {
                "start": customer["tw_start"],
                "end": customer["tw_end"]
            }
        })
    
    # Write to JSON file
    with open(output_file, 'w') as f:
        json.dump(instance, f, indent=2)
    
    print(f"JSON instance written to {output_file}")
    return instance

def main():
    # Set up directories with absolute paths
    cordeau_dir = r"c:\Users\ANAS\Desktop\VRP_uburu\instances\MDVRP\Cordeau-mdvrptw"
    output_dir = r"c:\Users\ANAS\Desktop\VRP_uburu\instances\MDHF-VRPTW-SPD\Taha-md-hf-vrptw-spd"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each pr0x file
    for i in range(1, 21):  # Process instances pr01 to pr20
        input_file = os.path.join(cordeau_dir, f"pr{i:02d}")
        
        try:
            # Get customer count from the original file
            with open(input_file, 'r') as f:
                first_line = f.readline().split()
                num_customers = int(first_line[2])
            
            # Output filename follows the required pattern: taha-{num_customers}_01.json
            output_file = os.path.join(output_dir, f"taha{i:02d}-n{num_customers}.json")
            
            # Transform the instance
            transform_instance_to_json(input_file, output_file)
            print(f"Successfully transformed pr{i:02d} to {output_file}")
        except FileNotFoundError:
            print(f"File not found: {input_file}")
        except Exception as e:
            print(f"Error transforming pr{i:02d}: {str(e)}")

if __name__ == "__main__":
    main()
