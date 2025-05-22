import csv
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import shutil
import logging

# Configure logging for debug (to file and console)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("driver_log_debug.log"),    # Log file for debug info
        logging.StreamHandler()                         # Console output handler
    ]
)

# Constants and configuration
DEFAULT_TIMEZONE = ZoneInfo("America/New_York")  # Default timezone for all datetimes (handles DST)
PAY_RATE_PER_MILE = 0.50                        # Pay rate per mile for company drivers (example)
OWNER_OPERATOR_PERCENTAGE = 0.80                # Percentage of revenue for owner-operator pay (example)

# Ensure necessary directories exist
os.makedirs("receipts", exist_ok=True)
os.makedirs("exports", exist_ok=True)

def log_trip():
    """
    Prompts the user for trip details and logs them to 'trips.csv'.
    Calculates driver pay based on driver type and records any trip expense.
    """
    try:
        # Gather trip details from user
        trip_id = input("Enter Trip ID: ").strip()
        driver_name = input("Enter Driver Name: ").strip()
        driver_type = input("Enter Driver Type (company/owner): ").strip().lower()
        start_time_str = input("Enter Start Time (YYYY-MM-DD HH:MM, local time): ").strip()
        end_time_str = input("Enter End Time (YYYY-MM-DD HH:MM, local time): ").strip()
        
        # Parse start and end times into datetime objects
        try:
            start_dt = datetime.fromisoformat(start_time_str)
            end_dt = datetime.fromisoformat(end_time_str)
        except Exception as e:
            logging.error("Invalid date/time format. Please use YYYY-MM-DD HH:MM. Error: %s", e)
            print("Error: Invalid date/time format. Trip not logged.")
            return  # Abort logging this trip due to input error
        
        # Assign timezone to datetimes (this will handle DST transitions automatically)
        start_dt = start_dt.replace(tzinfo=DEFAULT_TIMEZONE)
        end_dt = end_dt.replace(tzinfo=DEFAULT_TIMEZONE)
        
        # Calculate trip duration in hours
        duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        
        # Get mileage from user
        try:
            miles = float(input("Enter miles driven: ").strip())
        except ValueError:
            logging.error("Miles must be a numeric value.")
            print("Error: Miles must be a number. Trip not logged.")
            return
        
        # If owner-operator, get revenue for the trip to calculate pay
        revenue = 0.0
        if driver_type == "owner":
            try:
                revenue = float(input("Enter revenue for this trip (owner-operator): ").strip())
            except ValueError:
                logging.error("Revenue must be a numeric value.")
                print("Error: Revenue must be a number. Trip not logged.")
                return
        
        # Calculate pay based on driver type and inputs
        pay = calculate_pay(driver_type, miles, revenue)
        
        # Optionally log an expense associated with this trip
        expense_amount = 0.0
        expense_desc = ""
        add_expense = input("Any expense to log for this trip? (y/n): ").strip().lower()
        if add_expense == 'y':
            try:
                expense_amount = float(input("  Enter expense amount: ").strip())
            except ValueError:
                logging.error("Expense amount must be numeric.")
                print("Error: Expense amount must be a number. Expense not logged for trip.")
                expense_amount = 0.0
            else:
                expense_desc = input("  Enter expense description: ").strip()
                # Record the expense in the expenses CSV
                log_expense_record(driver_name or "General", expense_amount, expense_desc, start_dt.date())
        
        # Prepare data row and header for trips CSV
        header = ["TripID", "DriverName", "DriverType", "StartTime", "EndTime", 
                  "DurationHours", "Miles", "Pay", "ExpenseAmount", "ExpenseDescription"]
        data_row = [
            trip_id, 
            driver_name, 
            driver_type, 
            start_dt.isoformat(),    # ISO format includes date, time, and zone
            end_dt.isoformat(), 
            f"{duration_hours:.2f}", 
            f"{miles:.2f}", 
            f"{pay:.2f}", 
            f"{expense_amount:.2f}", 
            expense_desc
        ]
        
        # Write the trip record to CSV (append mode)
        write_to_csv("trips.csv", header, data_row)
        print(f"Trip {trip_id} logged successfully.")
        logging.info(f"Logged trip {trip_id} for driver {driver_name}.")
    except Exception as e:
        # Catch-all for any unexpected errors in this function to avoid crash
        logging.error("Unexpected error in log_trip: %s", e)
        print("An error occurred while logging the trip. Please check the log for details.")

def calculate_pay(driver_type, miles, revenue=0.0):
    """
    Calculates the pay for a trip based on driver type.
    - Company driver: paid a fixed rate per mile.
    - Owner-operator: paid a percentage of the trip revenue.
    """
    if driver_type == "company":
        return miles * PAY_RATE_PER_MILE
    elif driver_type == "owner":
        return revenue * OWNER_OPERATOR_PERCENTAGE
    else:
        logging.warning("Unknown driver type '%s'. Pay set to 0.", driver_type)
        return 0.0

def log_expense_record(driver_name, amount, description, date):
    """
    Logs a single expense record to 'expenses.csv'. 
    This is a helper function for internal use (does not prompt user).
    """
    header = ["Date", "DriverName", "Amount", "Description"]
    data_row = [date.isoformat(), driver_name, f"{amount:.2f}", description]
    write_to_csv("expenses.csv", header, data_row)
    logging.info(f"Expense logged: {driver_name} - ${amount:.2f} for {description}.")

def log_expense():
    """
    Prompts the user for an expense and logs it to 'expenses.csv'.
    This can be used for general expenses not tied to a specific trip.
    """
    try:
        driver_name = input("Enter Driver Name (or leave blank for general expense): ").strip()
        if driver_name == "":
            driver_name = "General"
        amount = float(input("Enter expense amount: ").strip())
        description = input("Enter expense description: ").strip()
        date_str = input("Enter date of expense (YYYY-MM-DD): ").strip()
        try:
            date = datetime.fromisoformat(date_str).date()
        except Exception:
            logging.error("Invalid date format for expense.")
            print("Error: Invalid date format. Use YYYY-MM-DD.")
            return
        # Log the expense record
        log_expense_record(driver_name, amount, description, date)
        print("Expense logged successfully.")
    except ValueError:
        logging.error("Expense amount must be numeric.")
        print("Error: Expense amount must be a number. Expense not logged.")
    except Exception as e:
        logging.error("Unexpected error in log_expense: %s", e)
        print("An error occurred while logging the expense.")

def upload_receipt():
    """
    Prompts for a file path to a receipt/document and copies the file into the 'receipts' directory.
    """
    file_path = input("Enter the path to the receipt/document file: ").strip()
    if not os.path.isfile(file_path):
        logging.error("Receipt upload failed - file not found: %s", file_path)
        print("Error: File not found. Please check the path and try again.")
        return
    try:
        # Copy the file into the receipts directory
        file_name = os.path.basename(file_path)
        dest_path = os.path.join("receipts", file_name)
        shutil.copy(file_path, dest_path)
        print(f"Receipt '{file_name}' uploaded to the 'receipts' folder.")
        logging.info(f"Uploaded receipt '{file_name}' to receipts directory.")
    except Exception as e:
        logging.error("Failed to upload receipt: %s", e)
        print("Error: Could not upload the file. Please check the log for details.")

def export_data():
    """
    Aggregates trip and expense data and outputs a summary CSV in the 'exports' directory.
    The summary includes total miles, total pay, and total expenses across all records.
    """
    try:
        total_miles = total_pay = total_expenses = 0.0
        # Sum up all trip miles and pay from trips.csv
        if os.path.exists("trips.csv"):
            with open("trips.csv", mode='r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        total_miles += float(row.get("Miles", 0) or 0)
                        total_pay += float(row.get("Pay", 0) or 0)
                    except ValueError:
                        continue  # Skip any rows with non-numeric data
        # Sum up all expenses from expenses.csv
        if os.path.exists("expenses.csv"):
            with open("expenses.csv", mode='r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        total_expenses += float(row.get("Amount", 0) or 0)
                    except ValueError:
                        continue
        # Prepare summary data
        summary_rows = [
            ["Total Miles", f"{total_miles:.2f}"],
            ["Total Pay", f"${total_pay:.2f}"],
            ["Total Expenses", f"${total_expenses:.2f}"]
        ]
        # Write summary to a CSV file
        summary_file = os.path.join("exports", "summary.csv")
        with open(summary_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Amount"])
            writer.writerows(summary_rows)
        print("Data export complete. Summary saved to 'exports/summary.csv'.")
        logging.info("Data exported successfully. Summary report generated.")
    except Exception as e:
        logging.error("Unexpected error in export_data: %s", e)
        print("An error occurred during data export. Check the log for details.")

def write_to_csv(filename, header, data_row):
    """
    Appends a single row of data to a CSV file. If the file does not exist, writes a header first.
    """
    try:
        file_exists = os.path.isfile(filename)
        with open(filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)  # write header if file is new
            writer.writerow(data_row)
    except Exception as e:
        logging.error("Failed to write to %s: %s", filename, e)
        print(f"Error: Could not write to {filename}. Please check permissions or path.")

def main_menu():
    """
    Displays a menu for the user to choose actions and calls the appropriate functions.
    """
    while True:
        print("\nDriver Log Menu:")
        print("1. Log a new trip")
        print("2. Log an expense")
        print("3. Upload a receipt/document")
        print("4. Export data (summary report)")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == '1':
            log_trip()
        elif choice == '2':
            log_expense()
        elif choice == '3':
            upload_receipt()
        elif choice == '4':
            export_data()
        elif choice == '5':
            print("Exiting Driver Log. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 1-5.")

# Run the menu if executed as a script
if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        logging.critical("Fatal error in main loop: %s", e)
        print("A critical error occurred. Please check 'driver_log_debug.log' for details.")
