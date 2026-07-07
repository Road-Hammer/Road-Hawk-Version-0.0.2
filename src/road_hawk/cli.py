from __future__ import annotations

from .services import (
    TripInput,
    bootstrap,
    ensure_driver,
    ensure_truck,
    export_trips_csv,
    fuel_efficiency_report,
    list_drivers,
    list_recent_trips,
    list_trucks,
    log_maintenance,
    log_trip,
)


def prompt_float(label: str, *, required: bool = True) -> float | None:
    while True:
        raw = input(f"{label}: ").strip()
        if not raw:
            return None if not required else _retry_required(label)
        try:
            return float(raw)
        except ValueError:
            print("Enter a valid number.")


def prompt_text(label: str, *, required: bool = True) -> str | None:
    while True:
        raw = input(f"{label}: ").strip()
        if raw:
            return raw
        if not required:
            return None
        print("This field is required.")


def _retry_required(label: str) -> float:
    print(f"{label} is required.")
    while True:
        raw = input(f"{label}: ").strip()
        try:
            return float(raw)
        except ValueError:
            print("Enter a valid number.")


def register_driver() -> None:
    driver_id = prompt_text("Driver ID")
    name = prompt_text("Driver name")
    if not driver_id or not name:
        return
    ensure_driver(driver_id, name)
    print(f"Driver {driver_id} saved.")


def register_truck() -> None:
    truck_number = prompt_text("Truck number")
    if not truck_number:
        return
    vin = prompt_text("VIN (optional)", required=False)
    make = prompt_text("Make (optional)", required=False)
    model = prompt_text("Model (optional)", required=False)
    year_raw = prompt_text("Year (optional)", required=False)
    year = int(year_raw) if year_raw and year_raw.isdigit() else None
    ensure_truck(truck_number, vin=vin, make=make, model=model, year=year)
    print(f"Truck {truck_number} saved.")


def record_trip() -> None:
    driver_id = prompt_text("Driver ID")
    truck_number = prompt_text("Truck number")
    miles = prompt_float("Miles driven")
    fuel = prompt_float("Fuel used (gallons)")
    if not driver_id or not truck_number or miles is None or fuel is None:
        return

    load_weight = prompt_float("Load weight in lbs (optional)", required=False)
    hours = prompt_float("Hours driven (optional)", required=False)
    fuel_price = prompt_float("Fuel price per gallon (optional)", required=False)
    location = prompt_text("Location (optional)", required=False)

    result = log_trip(
        TripInput(
            driver_id=driver_id,
            truck_number=truck_number,
            miles_driven=miles,
            fuel_used=fuel,
            load_weight=load_weight,
            hours_driven=hours,
            fuel_price=fuel_price,
            location=location,
        )
    )

    print(f"Trip logged. MPG: {result['mpg']:.2f}")
    if result["fuel_cost"] is not None:
        print(f"Fuel cost: ${result['fuel_cost']:.2f}")
    if result["avg_speed"] is not None:
        print(f"Avg speed: {result['avg_speed']:.2f} MPH")


def show_recent_trips() -> None:
    trips = list_recent_trips(limit=15)
    if not trips:
        print("No trips logged yet.")
        return

    print("\nRecent trips:")
    for trip in trips:
        print(
            f"  [{trip['logged_at']}] {trip['driver_id']} / {trip['truck_number']} "
            f"- {trip['miles_driven']} mi, {trip['fuel_used']} gal, "
            f"{trip['mpg']} MPG"
        )


def show_fuel_report() -> None:
    driver_id = prompt_text("Filter by driver ID (leave blank for all)", required=False)
    rows = fuel_efficiency_report(driver_id)
    if not rows:
        print("No fuel data available.")
        return

    print("\nFuel efficiency report:")
    for row in rows:
        print(
            f"  {row['driver_id']}: {row['trip_count']} trips, "
            f"{row['total_miles']} mi, {row['total_fuel']} gal, "
            f"avg {row['avg_mpg']} MPG"
        )


def record_maintenance() -> None:
    truck_number = prompt_text("Truck number")
    service_date = prompt_text("Service date (YYYY-MM-DD)")
    details = prompt_text("Service details")
    cost = prompt_float("Cost (optional)", required=False)
    if not truck_number or not service_date or not details:
        return

    ensure_truck(truck_number)
    record_id = log_maintenance(truck_number, service_date, details, cost)
    print(f"Maintenance record #{record_id} saved.")


def show_fleet() -> None:
    trucks = list_trucks()
    drivers = list_drivers()

    print("\nDrivers:")
    if drivers:
        for driver in drivers:
            print(f"  {driver['driver_id']} - {driver['name']}")
    else:
        print("  None registered")

    print("\nTrucks:")
    if trucks:
        for truck in trucks:
            label = " ".join(
                part
                for part in [truck.get("year"), truck.get("make"), truck.get("model")]
                if part
            )
            suffix = f" ({label})" if label else ""
            print(f"  {truck['truck_number']}{suffix}")
    else:
        print("  None registered")


def export_trips() -> None:
    path = export_trips_csv()
    print(f"Exported trips to {path}")


MENU = {
    "1": ("Register driver", register_driver),
    "2": ("Register truck", register_truck),
    "3": ("Log trip", record_trip),
    "4": ("View recent trips", show_recent_trips),
    "5": ("Fuel efficiency report", show_fuel_report),
    "6": ("Log maintenance", record_maintenance),
    "7": ("View fleet roster", show_fleet),
    "8": ("Export trips to CSV", export_trips),
    "9": ("Exit", None),
}


def main() -> None:
    bootstrap()
    print("Road Hawk v0.1 — built by a trucker, for truckers.")

    while True:
        print("\n==== Road Hawk ====")
        for key, (label, _) in MENU.items():
            print(f"{key}. {label}")

        choice = input("Select option: ").strip()
        if choice == "9":
            print("Rolling out. Stay safe.")
            break

        action = MENU.get(choice)
        if not action:
            print("Invalid choice.")
            continue

        _, handler = action
        if handler:
            handler()