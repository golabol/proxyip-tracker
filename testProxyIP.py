import os
import shutil
import subprocess
import zipfile
from pathlib import Path
import argparse

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

def find_matching_files(directory, pattern):
    """Find all files matching the pattern in a directory."""
    return list(directory.glob(pattern))

def combine_files(input_files, output_file):
    """Combine multiple files into one."""
    with open(output_file, 'w') as outfile:
        for file_path in input_files:
            with open(file_path, 'r') as infile:
                shutil.copyfileobj(infile, outfile)

def run_iptest(iptest_path, input_file, port, tls_mode, max_processes, output_file, speed_test_threads):
    """Run iptest with given parameters."""
    iptest_command = [
        f"{iptest_path}",
        f"-file={input_file}",
        f"-port={port}",
        f"-tls=true",
        f"-max={max_processes}",
        f"-outfile={output_file}",
        f"-speedtest={speed_test_threads}",
    ]
    print(f"Running command: {' '.join(iptest_command)}")
    subprocess.run(iptest_command)

def main(
    txt_dir="txt",
    txt_zip="txt.zip",
    zip_url="https://zip.baipiao.eu.org",
    region="0",
    tls_mode="1",
    port="443",
    max_processes="100",
    output_file="ip.csv",
    speed_test_threads="0"
):
    """Main function to orchestrate the script."""
    current_dir = Path(__file__).parent
    txt_dir_path = current_dir / txt_dir
    txt_zip_path = current_dir / txt_zip
    iptest_path = current_dir / "iptest.exe"
    curl_path = current_dir / "curl.exe"

    # Setup: Clear directory and handle txt.zip
    clear_directory(txt_dir_path)

    print("Downloading txt.zip...")
    download_file(curl_path, zip_url, txt_zip_path)

    extract_zip(txt_zip_path, txt_dir_path)

    # Determine input files based on REGION
    if region == "0":
        input_files = find_matching_files(txt_dir_path, f"*-{tls_mode}-{port}.txt")
        if not input_files:
            print(f"No files found for pattern: *-{tls_mode}-{port}.txt")
            return
        combined_file = txt_dir_path / "combined.txt"
        print(f"Combining {len(input_files)} files into {combined_file}")
        combine_files(input_files, combined_file)
        input_file = combined_file
    else:
        input_files = find_matching_files(txt_dir_path, f"{region}-{tls_mode}-{port}.txt")
        if not input_files:
            print(f"No file found for pattern: {region}-{tls_mode}-{port}.txt")
            return
        input_file = input_files[0]

    # Run iptest with predefined inputs
    run_iptest(iptest_path, input_file, port, tls_mode, max_processes, output_file, speed_test_threads)

    # Cleanup
    clear_directory(txt_dir_path)
    print(f"Testing completed. Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run IP test script.")
    parser.add_argument("--txt_dir", default="txt", help="Directory for txt files.")
    parser.add_argument("--txt_zip", default="txt.zip", help="Name of the zip file.")
    parser.add_argument("--zip_url", default="https://zip.baipiao.eu.org", help="URL to download the zip file.")
    parser.add_argument("--region", default="0", help="Region code.")
    parser.add_argument("--tls_mode", default="1", help="TLS mode.")
    parser.add_argument("--port", default="443", help="Port to test.")
    parser.add_argument("--max_processes", default="100", help="Maximum number of processes.")
    parser.add_argument("--output_file", default="ip.csv", help="Output file name.")
    parser.add_argument("--speed_test_threads", default="0", help="Number of threads for speed test.")
    args = parser.parse_args()

    main(
        txt_dir=args.txt_dir,
        txt_zip=args.txt_zip,
        zip_url=args.zip_url,
        region=args.region,
        tls_mode=args.tls_mode,
        port=args.port,
        max_processes=args.max_processes,
        output_file=args.output_file,
        speed_test_threads=args.speed_test_threads
    )
