# transform_instances.py Documentation

## Overview

`transform_instances.py` is a Python script that transforms Cordeau's MDVRPTW instances into Multi-Depot Heterogeneous Fleet Vehicle Routing Problem with Time Windows and Simultaneous Pickup and Delivery (MDHF-VRPTW-SPD) format. This transformation creates realistic e-commerce delivery scenarios with combined deliveries and returns.

## Key Features

- Converts standard Cordeau MDVRPTW instances to MDHF-VRPTW-SPD format
- Adds pickup quantities based on customer categories
- Splits service times between pickup and delivery operations
- Generates a heterogeneous fleet with four vehicle types
- Preserves original depot locations and time windows
- Adjusts time windows when necessary for increased service times

## Configuration Parameters

The script uses these key parameters (all can be customized):

```python
# Fixed random seed (for reproducibility)
RANDOM_SEED = 42

# Service time factors
PICKUP_HANDLING_FACTOR = 0.5  # Additional time per pickup item
BASE_OPERATION_TIME_FACTOR = 0.2  # Base operations time factor

# Customer category distribution
CATEGORY_A_THRESHOLD = 0.70  # Delivery + low return
CATEGORY_B_THRESHOLD = 0.90  # Delivery + significant return
# Category C = Return-only (remaining 10%)

# Pickup quantity factors
CATEGORY_A_PICKUP_MIN = 0.05  # Min 5% of delivery quantity
CATEGORY_A_PICKUP_MAX = 0.20  # Max 20% of delivery quantity
CATEGORY_B_PICKUP_MIN = 0.20  # Min 20% of delivery quantity
CATEGORY_B_PICKUP_MAX = 0.50  # Max 50% of delivery quantity
```

## Transformation Process

### 1. Input Parsing
- Reads Cordeau MDVRPTW instances from standard text files
- Extracts depot information, customer data, and time windows
- Handles both Type 6 (MDVRPTW) and Type 2 (MDVRP) instances

### 2. Customer Categorization
Customers are randomly assigned to one of three categories:
- **Category A (70%)**: Delivery with low return rate
- **Category B (20%)**: Delivery with significant return
- **Category C (10%)**: Return-only customers

### 3. Pickup/Delivery Quantity Generation
- **Category A**: Original delivery quantity + small pickup (5-20% of delivery)
- **Category B**: Original delivery quantity + larger pickup (20-50% of delivery)
- **Category C**: Zero delivery, small pickup (1-3 units)
- Safety check to ensure combined quantities don't exceed smallest vehicle capacity

### 4. Service Time Splitting
For each customer, the script:
1. Calculates a base operation time for positioning/paperwork
2. Divides remaining service time proportionally based on delivery/pickup quantities
3. Adds extra handling time for pickup operations (0.5 min per item)
4. Creates separate delivery_service_time and pickup_service_time values
5. Adjusts time windows if the new combined service time exceeds the original window

### 5. Heterogeneous Fleet Generation
Creates four vehicle classes per depot with varying capacities:

| Class | Vehicle Type         | Capacity   | Fixed Cost | Variable Cost |
|-------|---------------------|------------|------------|---------------|
| 1     | Cargo bike/micro-EV | 0.25 × Q*  | 60         | 0.45          |
| 2     | Small van (1 t)     | 0.50 × Q*  | 120        | 0.60          |
| 3     | Large van (2 t)     | 0.80 × Q*  | 180        | 0.75          |
| 4     | 7.5-t truck         | 1.20 × Q*  | 240        | 0.90          |

*Where Q* is the original vehicle capacity from Cordeau's instance.

## Output Format

The script generates text files in a structured format:
```
7 999 n d 4         # Format: type=7, unlimited vehicles, n customers, d depots, 4 vehicle classes
D1 Q1a FC1 VC1      # Depot 1, vehicle type 1: Duration, Capacity, FixedCost, VariableCost
D1 Q1b FC2 VC2      # Depot 1, vehicle type 2
D1 Q1c FC3 VC3      # Depot 1, vehicle type 3
D1 Q1d FC4 VC4      # Depot 1, vehicle type 4
D2 Q2a FC1 VC1      # Depot 2, vehicle type 1
...
i x y st D P e l    # Customer i: coords(x,y), total service time, delivery qty, pickup qty, time window(e,l)
...
id x y 0 0 0 0 0    # Depot coordinates
```

The service time (st) in the output represents the combined total of delivery_service_time and pickup_service_time.

## Usage

Run the script directly with Python:

```powershell
python transform_instances.py
```

This will process all available Cordeau MDVRPTW problems (pr01-pr20) and generate transformed instances in the `Taha-md-hf-vrptw-spd` directory.

## Key Implementation Details

1. **Split Service Times**: The script implements sophisticated service time calculation that separates the time required for delivery operations from pickup operations:
   - Each operation has a base time component
   - Proportional time allocation based on item quantities
   - Extra handling time for return/pickup items

2. **Time Window Adjustment**: When the new total service time exceeds the original time window, the script automatically extends the window's end time to ensure feasibility.

3. **Fixed Random Seed**: All random operations use a fixed seed (42) for reproducibility of results.

4. **Flexible Instance Handling**: The script can process both MDVRPTW (type 6) and MDVRP (type 2) instances, automatically creating time windows for the latter.

