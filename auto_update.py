import os

import shutil

import time

import difflib



# === CONFIGURATION SETTINGS ===

WATCH_FOLDER = "./"  # Monitors the current folder

BACKUP_FOLDER = "./backups/"  # Stores backup files

MAIN_FILE = "Road_Hawk.py"  # Main Road Hawk program



# === ENSURE BACKUP DIRECTORY EXISTS ===

if not os.path.exists(BACKUP_FOLDER):

    os.makedirs(BACKUP_FOLDER)



# === FUNCTION: BACKUP CURRENT FILE ===

def backup_current_version():

    """Creates a backup of the current Road_Hawk.py before updating."""

    timestamp = time.strftime("%Y%m%d-%H%M%S")

    backup_path = os.path.join(BACKUP_FOLDER, f"Road_Hawk_{timestamp}.bak")

    shutil.copy(MAIN_FILE, backup_path)

    print(f"✅ Backup saved: {backup_path}")



# === FUNCTION: DETECT CHANGES ===

def detect_changes(new_code):

    """Compares current Road_Hawk.py with new update files."""

    if not os.path.exists(MAIN_FILE):

        return True  # If the file doesn't exist, assume it's a fresh install



    with open(MAIN_FILE, "r", encoding="utf-8") as old_file:

        old_code = old_file.readlines()



    diff = list(difflib.unified_diff(old_code, new_code.splitlines(keepends=True)))

    return diff if diff else None



# === FUNCTION: UPDATE CODE AUTOMATICALLY ===

def update_code(new_code):

    """Updates Road_Hawk.py only if changes are detected."""

    changes = detect_changes(new_code)



    if changes:

        print("\n🔄 Changes detected! Updating Road Hawk system...\n")

        backup_current_version()



        # Apply the update

        with open(MAIN_FILE, "w", encoding="utf-8") as file:

            file.write(new_code)



        print("✅ Update successful! Road_Hawk.py has been refreshed.\n")

    else:

        print("🚀 No changes detected. Road Hawk is already up to date.\n")



# === FUNCTION: MONITOR FILE DROP ===

def monitor_folder():

    """Watches for new updates dropped into the folder."""

    print("\n🚛 Road Hawk Auto-Update is running... Drop new updates into the folder.\n")



    while True:

        time.sleep(5)  # Check every 5 seconds



        for file in os.listdir(WATCH_FOLDER):

            if file.endswith(".update.py"):

                update_path = os.path.join(WATCH_FOLDER, file)



                with open(update_path, "r", encoding="utf-8") as new_file:

                    new_code = new_file.read()



                update_code(new_code)



                # Remove update file after applying changes

                os.remove(update_path)

                print(f"🗑 Deleted processed update file: {file}")



# === RUN THE MONITORING SYSTEM ===

if __name__ == "__main__":

    monitor_folder()
import os

import shutil

import time



# Folders

BACKUP_FOLDER = "backups"

ARCHIVE_FOLDER = "archive"

MAIN_SCRIPT = "Road_Hawk.py"



# Ensure folders exist

def setup_folders():

    for folder in [BACKUP_FOLDER, ARCHIVE_FOLDER]:

        if not os.path.exists(folder):

            os.makedirs(folder)

            print(f"📂 Created folder: {folder}")



def monitor_folder():

    print("🚀 Road Hawk Auto-Update is running... Drop new updates into the folder.")



    while True:

        files = os.listdir(BACKUP_FOLDER)

        for file in files:

            update_path = os.path.join(BACKUP_FOLDER, file)

            

            if file.endswith(".py"):

                apply_python_update(update_path)

            elif file.endswith((".txt", ".docx")):

                print(f"📌 Update file detected: {file} - Manual review required.")

                archive_file(update_path)  # Moves it for later review



        time.sleep(5)  # Check every 5 seconds



def apply_python_update(update_path):

    print(f"🔄 Processing Python update: {update_path}")



    # Step 1: Backup the existing script

    timestamp = time.strftime("%Y%m%d-%H%M%S")

    backup_path = os.path.join(ARCHIVE_FOLDER, f"{MAIN_SCRIPT}_{timestamp}.bak")

    

    if os.path.exists(MAIN_SCRIPT):

        shutil.copy(MAIN_SCRIPT, backup_path)

        print(f"✅ Previous version saved to: {backup_path}")



    # Step 2: Replace with the new update

    shutil.move(update_path, MAIN_SCRIPT)

    print(f"✅ Update applied: {MAIN_SCRIPT} updated successfully!")



def archive_file(file_path):

    """ Move text/Word documents to the archive folder for manual review """

    new_location = os.path.join(ARCHIVE_FOLDER, os.path.basename(file_path))

    shutil.move(file_path, new_location)

    print(f"📂 Moved {file_path} to {new_location} for review.")



# Run the monitoring system

if __name__ == "__main__":

    setup_folders()  # Ensure folders exist before running

    monitor_folder()

  