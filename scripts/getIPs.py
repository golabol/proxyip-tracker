import requests
import zipfile
import io
import fnmatch
import configparser
import json
import re

countries = {
    "ID": "Indonesia",
    "SG": "Singapore",
    "JP": "Japan",
    "AT": "Austria",
    "US": "United States",
    "MY": "Malaysia",
    "CA": "Canada",
    "GB": "United Kingdom",
    "IN": "India",
    "IR": "Iran",
    "AE": "United Arab Emirates",
    "FI": "Finland",
    "TR": "Turkey",
    "MD": "Moldova",
    "TW": "Taiwan",
    "CH": "Switzerland",
    "SE": "Sweden",
    "NL": "Netherlands",
    "ES": "Spain",
    "RU": "Russia",
    "RO": "Romania",
    "PL": "Poland",
    "MX": "Mexico",
    "AL": "Albania",
    "IT": "Italy",
    "DE": "Germany",
    "NZ": "New Zealand",
    "FR": "France",
    "AM": "Armenia",
    "CY": "Cyprus",
    "DK": "Denmark",
    "BR": "Brazil",
    "KR": "South Korea",
    "VN": "Vietnam",
    "TH": "Thailand",
    "HK": "Hong Kong",
    "CN": "China",
    "AU": "Australia",
    "AR": "Argentina",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "AZ": "Azerbaijan",
    "CO": "Colombia",
    "CZ": "Czech Republic",
    "EE": "Estonia",
    "GI": "Gibraltar",
    "IE": "Ireland",
    "HU": "Hungary",
    "IL": "Israel",
    "KZ": "Kazakhstan",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "PH": "Philippines",
    "PT": "Portugal",
    "PR": "Puerto Rico",
    "QA": "Qatar",
    "RS": "Serbia",
    "SC": "Seychelles",
    "SA": "Saudi Arabia",
    "SK": "Slovakia",
    "UA": "Ukraine",
    "UZ": "Uzbekistan",
    "T1": "Unknown"
}
tls_ports = {
    443,
    2053,
    2083,
    2087,
    2096,
    8443
}
nontls_ports = {
    80,
    2052,
    2082,
    2086,
    2095,
    8080
}
added_ips = set()

def download_zip_file(url):
    """Download the ZIP file from the specified URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"Error during file download: {e}")

def extract_and_combine_files(zip_file, file_pattern):
    """Extract and combine content of files matching the pattern."""
    global added_ips
    matching_files = fnmatch.filter(zip_file.namelist(), file_pattern)
    if not matching_files:
        raise FileNotFoundError(f"No files matching {file_pattern} found in the ZIP archive.")

    combined_content = []
    for file_name in matching_files:
        pattern = r"(\d+)-([0-1])-(\d+)\.txt"
        match = re.match(pattern, file_name)
        asn, tls, port = match.groups()
        with zip_file.open(file_name) as file:
            lines = file.read().decode('utf-8').splitlines()
            for line in lines:
                ip = line.strip()
                if ip and ip not in added_ips:
                    combined_content.append({'ip': ip, 'asn': asn, 'tls': 'YES' if tls == '1' else 'NO', 'port': int(port)})
                    added_ips.add(ip)

    return combined_content

def save_to_file(content, output_file):
    """Save the combined content to a file."""
    with open(output_file, 'w') as file:
        file.write(content)
    print(f"Combined content saved to: {output_file}")

def get_country_based_ips():
    global added_ips
    location_ips_data = []
    base_url = 'https://cfip.ashrvpn.v6.army/?country='
    for con in countries:
        try:
            response = requests.get(base_url + con)
            response.raise_for_status()
            if response.text:
                for line in response.text.split('\n'):
                    ip, port = line.split('|')[0].strip().split(':')
                    if ip not in added_ips:
                        location_ips_data.append({
                            'ip': ip,
                            'port': int(port),
                            'country': con
                        })
                        added_ips.add(ip)
        except requests.exceptions.RequestException as e:
            raise SystemExit(f"Error during access to {base_url+con}: {e}")
        except Exception as e:
            print(f"Error during parsing '{base_url+con}' content: {e}")
    return location_ips_data

def process_zip_file(url, file_pattern, output_file):
    """Main function to download, process, and save the combined content."""
    print(f"Downloading ZIP file from: {url}")
    zip_data = download_zip_file(url)
    country_based_ips_data = get_country_based_ips()

    with zipfile.ZipFile(zip_data) as zip_file:
        print("Extracting and combining files...")
        combined_content = extract_and_combine_files(zip_file, file_pattern)
        for item in country_based_ips_data:
            combined_content.append({
                'ip': item.get('ip'),
                'asn': None,
                'tls': 'YES' if item.get('port') in tls_ports else 'NO' if item.get('port') in nontls_ports else 'Unknown',
                'port': item.get('port'),
            })
        print("Saving combined content to file...")
        save_to_file(json.dumps(combined_content, indent=2), output_file)

def load_config(config_file):
    """Load configuration from a file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['getIPs']

# Usage example
if __name__ == "__main__":
    config_file = "config.ini"  # Path to your config file

    try:
        # Load configuration
        config = load_config(config_file)
        url = config.get('url')
        file_pattern = config.get('file_pattern')
        output_file = config.get('output_file')

        # Process the ZIP file
        process_zip_file(url, file_pattern, output_file)
    except Exception as e:
        print(e)
