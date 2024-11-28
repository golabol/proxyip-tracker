import os
import shutil
import subprocess
import zipfile
from pathlib import Path

# Helper functions
def clear_directory(dir_path):
    """Clear a directory if it exists."""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def download_file(curl_path, url, dest):
    """Download a file using curl."""
    subprocess.run([f"{curl_path}", "-#", url, "-o", dest], check=True)

def extract_zip(file_path, extract_to):
    """Extract a ZIP file."""
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def get_user_input(prompt, default=None):
    """Prompt user for input with a default value."""
    user_input = input(f"{prompt} (Default: {default}): ")
    return user_input.strip() or default

def list_txt_files(directory, pattern=""):
    """List .txt files matching a pattern in a directory."""
    return [f.name for f in Path(directory).glob(f"*{pattern}*.txt")]

# Initial setup
current_dir = Path(__file__).parent
txt_dir = current_dir / "txt"
txt_zip = current_dir / "txt.zip"
iptest_path = current_dir / "iptest.exe"
curl_path = current_dir / "curl.exe"

clear_directory(txt_dir)

# Download and update txt.zip if necessary
if txt_zip.exists():
    update_zip = get_user_input("Update local txt.zip data? 0: No update, 1: Update", "0")
    if update_zip == "1":
        download_file(curl_path, "https://zip.baipiao.eu.org", txt_zip)
else:
    print("Downloading txt.zip...")
    download_file(curl_path, "https://zip.baipiao.eu.org", txt_zip)

# Extract the ZIP file
extract_zip(txt_zip, txt_dir)

# Main menu
while True:
    print("\n1. Autonomous region or area mode")
    print("2. Custom port mode")
    print("0. Exit")
    menu_option = get_user_input("Please choose a mode", "2")

    if menu_option == "0":
        print("Exiting...")
        break

    if menu_option == "1":
        # Autonomous region or area mode
        print("\nAvailable autonomous regions or areas:")
        txt_files = list_txt_files(txt_dir)
        regions = set(f.split('-')[0] for f in txt_files)
        print("\n".join(regions))
        region = get_user_input("Enter a region from the list above", "45102")

        tls_files = [f for f in txt_files if f.startswith(f"{region}-")]
        tls_options = {f.split('-')[1] for f in tls_files}
        tls_mode = "1" if len(tls_options) == 1 else get_user_input("Enable TLS? 0: No, 1: Yes", "1")

        available_ports = [f.split('-')[2].split('.')[0] for f in tls_files if f.split('-')[1] == tls_mode]
        print("\nAvailable ports:")
        print("\n".join(available_ports))
        port = get_user_input("Enter the port to test", available_ports[0] if available_ports else "default")
    elif menu_option == "2":
        # Custom port mode
        tls_mode = get_user_input("Enable TLS? 0: No, 1: Yes", "1")
        available_ports = list_txt_files(txt_dir, f"-{tls_mode}-")
        ports = {f.split('-')[2].split('.')[0] for f in available_ports}
        print("\nAvailable ports:")
        print("\n".join(ports))
        port = get_user_input("Enter the port to test", next(iter(ports), "default"))

        shutil.copy(next(txt_dir.glob(f"*{tls_mode}-{port}.txt")), txt_dir / "ip.txt")

    # Testing parameters
    max_processes = int(get_user_input("Maximum concurrent processes", "100"))
    output_file = get_user_input("Output file name", "ip.csv")
    speed_test = int(get_user_input("Download speed test threads (0 to disable)", "2"))
    ip_file = f"{region}-{tls_mode}-{port}.txt" if menu_option == "1" else "ip.txt"

    # Run the iptest command
    iptest_command = [
        f"{iptest_path}",
        f"-file={txt_dir / ip_file}",
        f"-port={port}",
        f"-tls={'true' if tls_mode == '1' else 'false'}",
        f"-max={max_processes}",
        f"-outfile={output_file}",
        f"-speedtest={speed_test}",
    ]
    subprocess.run(iptest_command)

    # Post-processing for limiting IPs
    if speed_test > 0:
        limit_ips = get_user_input("Limit the number of tested IPs? 0: No, 1: Yes", "1") == "1"
        if limit_ips:
            limit = int(get_user_input("Sort by latency and test up to this many IPs", "20"))
            temp_file = current_dir / "temp"
            shutil.copy(output_file, temp_file)
            sorted_ips = []
            with open(temp_file) as f:
                for line in f:
                    if "ms" in line and len(sorted_ips) < limit:
                        sorted_ips.append(line.strip())

            with open(temp_file, "w") as f:
                f.write("\n".join(sorted_ips))

            subprocess.run([
                f"{iptest_path}",
                f"-file={temp_file}",
                f"-port={port}",
                f"-tls={'true' if tls_mode == '1' else 'false'}",
                f"-max={max_processes}",
                f"-outfile={output_file}",
                f"-speedtest={speed_test}",
            ])
            os.remove(temp_file)

    print(f"Testing completed. Results saved to {output_file}")

# Cleanup
clear_directory(txt_dir)
print("Done!")
