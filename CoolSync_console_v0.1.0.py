import os
import time
import shutil
import subprocess

# Default values for testing
DEFAULT_SOURCE_DIR = r'C:\Users\MindEye\Documents\Code\Python_code\Test_folder\Source_files'
DEFAULT_DEST_DIR = r'C:\Users\MindEye\Documents\Code\Python_code\Test_folder\Dest_files'
DEFAULT_START_TEMP = 30  # Example start temperature in Celsius
DEFAULT_STOP_TEMP = 50  # Updated default stop temperature in Celsius

# Function to get user input for directories and temperatures
def get_user_input():
    print("Please provide the following details or press Enter to use defaults.")
    source_dir = input(f"Enter the source directory path [{DEFAULT_SOURCE_DIR}]: ") or DEFAULT_SOURCE_DIR
    dest_dir = input(f"Enter the destination directory path [{DEFAULT_DEST_DIR}]: ") or DEFAULT_DEST_DIR
    start_temp = input(f"Enter the start temperature (in Celsius) [{DEFAULT_START_TEMP}]: ") or DEFAULT_START_TEMP
    stop_temp = input(f"Enter the stop temperature (in Celsius) [{DEFAULT_STOP_TEMP}]: ") or DEFAULT_STOP_TEMP
    return source_dir, dest_dir, float(start_temp), float(stop_temp)

# Function to get drive letters from paths
def get_drive_letters(paths):
    drive_letters = set()
    for path in paths:
        drive_letters.add(os.path.splitdrive(path)[0])
    return list(drive_letters)

# Function to get the drive's current temperature using smartctl
def get_drive_temperature(drive_letter):
    try:
        result = subprocess.run(['smartctl', '-A', f'{drive_letter}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise Exception(f"smartctl error: {result.stderr}")
        
        for line in result.stdout.split('\n'):
            if 'Temperature_Celsius' in line or 'Temperature' in line:
                # Extract the temperature value using regex
                import re
                match = re.search(r'(\d+)', line)
                if match:
                    temp = int(match.group(1))
                    return temp
                else:
                    raise Exception("Temperature value not found")
    except Exception as e:
        print(f"Error getting temperature for drive {drive_letter}: {e}")
        return None

# Function to perform mirror sync
def mirror_sync(source_dir, dest_dir, script_dir):
    # Copy new and updated files from source to destination
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, os.path.relpath(src_file, source_dir))
            dest_dir_path = os.path.dirname(dest_file)
            os.makedirs(dest_dir_path, exist_ok=True)
            shutil.copy2(src_file, dest_file)
    
    # Delete files and directories from destination that are not in source
    for root, dirs, files in os.walk(dest_dir):
        for file in files:
            dest_file = os.path.join(root, file)
            src_file = os.path.join(source_dir, os.path.relpath(dest_file, dest_dir))
            if not os.path.exists(src_file):
                os.remove(dest_file)
                
        for dir in dirs:
            dest_dir_path = os.path.join(root, dir)
            src_dir_path = os.path.join(source_dir, os.path.relpath(dest_dir_path, dest_dir))
            if not os.path.exists(src_dir_path) and dest_dir_path != script_dir:
                shutil.rmtree(dest_dir_path)

def monitor_and_backup(source_dir, dest_dir, start_temp, stop_temp):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if source and destination directories are valid
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return
    if not os.path.exists(dest_dir):
        print(f"Error: Destination directory '{dest_dir}' does not exist.")
        return

    # Get drive letters from source and destination paths
    drive_letters = get_drive_letters([source_dir, dest_dir])

    # Confirmation prompt
    print("\nConfiguration Summary:")
    print(f"Source Directory: {source_dir}")
    print(f"Destination Directory: {dest_dir}")
    print(f"Start Temperature: {start_temp}°C")
    print(f"Stop Temperature: {stop_temp}°C")
    print(f"Monitoring Drives: {', '.join(drive_letters)}")
    proceed = input("Do you want to proceed with the backup? (_Y_/_N_): ").lower()
    if proceed not in ['yes', 'y']:
        print("Backup canceled.")
        return

    backup_in_progress = False

    while True:
        for drive_letter in drive_letters:
            temp = get_drive_temperature(drive_letter)
            if temp is None:
                print(f"Error: Could not get the temperature for drive {drive_letter}.")
                return
            
            print(f"Current temperature for drive {drive_letter}: {temp}°C")

            if temp <= start_temp:
                if not backup_in_progress:
                    print("Temperature is within safe range. Starting backup...")
                    backup_in_progress = True
                    mirror_sync(source_dir, dest_dir, script_dir)
                    backup_in_progress = False
                    print("Backup process finished.")
                    return  # Exit after backup completes
            elif temp >= stop_temp:
                if backup_in_progress:
                    print("Temperature is too high. Pausing backup...")
                    backup_in_progress = False
                print("Waiting for temperature to drop within the safe range...")

        time.sleep(60)  # Wait 60 seconds before checking the temperature again

if __name__ == "__main__":
    source_dir, dest_dir, start_temp, stop_temp = get_user_input()
    monitor_and_backup(source_dir, dest_dir, start_temp, stop_temp)