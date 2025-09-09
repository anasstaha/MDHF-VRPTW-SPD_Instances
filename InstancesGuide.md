
# Step-by-Step Guide: Converting Cordeau’s **pr01 / pr02** MDVRPTW Instances into Deterministic MDHF-VRPTW-SPD Benchmarks for E-Commerce

---



## 1. Extract base data

### 1.1 Action

1. Read the first line of pr01/pr02 (`type m n t`).
1. Store: number of depots `t`, number of customers `n`, and depot lines (the last*t*records).
1. Copy each customer’s: coordinates (x_i,y_i), service duration  d_i, delivery demand D_i, original time-window [e_i,l_i].

### 1.2 Details & Formulas

* These fields are already present in Cordeau’s format (see*readme.txt* ).

### 1.3 File-editing Tip

* Keep a CSV or JSON table for easier manipulation.

---



## 2. Split customers into demand categories (SPD)

### 2.1 Action

1. For every customer i:
   draw a pseudo-random value u_i∈[0,1] with a fixed seed for reproducibility.
2. Assign demand type:
   • Category A : `(delivery + low return)` if u_i<0.70.
   • Category B : `(delivery + significant return)` if 0.70≤ u_i <0.90.
   • Category C : `(return-only)` if u_i ≥ 0.90.

### 2.2 Details & Formulas

* Mirrors e-commerce, where most stops are deliveries, some include returns, and a small share are pure returns.

### 2.3 File-editing Tip

* Record the seed in a comment block of your new instance.

---



## 3. Generate pickup  & delivery quantities

### 3.1 Action

1. Category A : keep original D_i; set pickup P_i=⌈ρ_iD_i⌉ with ρ_i∼U[0.05,0.20]
2. Category B : keep original D_i; set pickup P_i=⌈ρ_iD_i⌉ with ρ_i∼U[0.20,0.50]
3. Category C : set D_i=0; draw P_i∼U{1,3}.
4. Ensure D_i+P_i≤Q_min (the smallest vehicle capacity). If violated, scale P_i down.

### 3.2 Details & Formulas

* Total pickup ≈ 20–25 % of total deliveries, consistent with typical e-commerce return rates.

### 3.3 File-editing Tip

* Add two new columns in your data file: `pickup_qty` and `delivery_qty`.

---



## 4. Define a 4-class heterogeneous fleet

### 4.1 Action

Capacities relative to original single-type Q^*; costs reflect last-mile practice.


Class | Typical vehicle   |  Capacity Q_k

1 |  Cargo bike/micro-EV   |  0.25 Q^∗

2 |  Small van (1 t) |  0.50 Q^∗

3 | Large van (2 t) | 0.80 Q^∗

4 | 7.5-t truck |  1.20 Q^∗

* Fixed cost F_**k :** F_k=60+60(k−1)
* Variable cost α_**k  :** α_k=0.45+0.15(k−1)


### 4.3 File-editing Tip

* Switch to the heterogeneous-fleet format: type 7 = MDHF-VRPTW-SPD, example :
  • 7 999  n  4          ← header: type=7 (site-dependent VRPTW), t=4 classes
  • Class1   D  Q1       ← cargo bike / micro-EV
  • Class2   D  Q2       ← small van
  • Class3   D  Q3       ← large van
  • Class4   D  Q4       ← 7.5-t truck
  • ...                  ← customer lines (0…n-1)
  • ...                  ← depot lines (one per depot)

---



## 5. Time-Window and Service-Time Rules for Simultaneous Pickup & Delivery

### 5.1 Action

1. **Time windows:** keep Cordeau’s original [e_i,l_i] unchanged.
2. service duration : Define new service time  d_i^*=d_i+θP_i, where d_i is Cordeau’s original delivery duration, P_i the pickup quantity, and θ a per-item return-handling factor (e.g. 0.5 min per parcel).

   • If P_i=0 (pure delivery), d_i^*=d_i
   • If D_i=0 (return-only), still use Cordeau’s  d_i as a base—representing hand-off paperwork—plus the pickup term.
3. Feasibility check : if e_i+d_i^>l_i , shift l_i forward just enough to fit d_i^*.

### 5.2 Details & Formulas

* Captures extra handling for returns without altering promised windows except when strictly necessary.

### 5.3 File-editing Tip

* Update service-time field; edit lil_i**l**i only when shifted.

---



## 6. Preserve depot data

### 6.1 Action

1. Keep depot coordinates & route-duration D. (Depots retain original roles.)
2. Looking at the Cordeau instances (like pr01), which specify "2 vehicles per depot" in the homogeneous case, your heterogeneous extension would:

   1. Replace this with multiple vehicle types at each depot
   2. Let the algorithm determine how many of each to use based on costs
   3. Still specify the key vehicle parameters (capacity, costs, duration limits) for each type
