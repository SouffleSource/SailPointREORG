# SailPointREORG

This project helps teams manage organizational changes by analyzing identity information, roles, entitlements, and access during departmental reorganizations. The tool connects to SailPoint IdentityNow to gather comprehensive identity data and generate reports that assist in the smooth transition of personnel between departments and teams.

## Project Structure

- **api_connection.py**: Contains functions to obtain access tokens and create connection headers for the SailPoint API.
- **main.py**: Script to process organizational changes from a CSV file and extract identity details.
- **export.py**: Functions to export identity data, entitlements, and roles to CSV and Excel files.
- **.env**: Environment variables for API credentials and base URL.
>[!NOTE]
> `.env` files are used to store environment variables in key-value pairs for applications, helping manage configuration settings without hardcoding them into source code. They enhance security by keeping sensitive information like API keys and database credentials out of version control systems
- **README.md**: Project documentation.

## Prerequisites

- Python 3.8 or higher
- SailPoint IdentityNow tenant with API access
- Client ID and Client Secret for API authentication
- CSV file containing reorganization data (`reorg.csv`)

## Setup

1. Clone the repository.
2. Create a `.env` file in the root directory with the following content:
    ```env
    CLIENT_ID={your_client_id}
    CLIENT_SECRET={your_client_secret}
    BASE_URL=https://tenantname.api.identitynow.com/
    CERT_PATH=path/to/your/cert.pem
    ```
> [!NOTE] 
> You only need to configure CERT_PATH if your organization uses SSL/TLS inspection on its firewalls.

3. Create a CSV file named `reorg.csv` with the following columns:
   - Payroll ID
   - Employee Name
   - Position
   - Current Department ID
   - New Department ID
   - Current Team ID
   - New Team ID

## Usage

### Process Reorganization Data

To process organizational changes and generate reports, run:
```sh
python main.py
```

This script will:
- Load identity information from `reorg.csv`
- Retrieve detailed identity information from SailPoint for each person
- Collect roles, accounts, and entitlements for each identity
- Validate department and team IDs match between the CSV and API data
- Generate detailed reports on entitlements and roles
- Save the collected data to `all_identities.json`

## Reports Generated

The `export.py` module provides functions to export identity data in various formats:

- **Identity Entitlements Report**: Exports all identity entitlements to `reports/all_identities_entitlements.csv`
- **Role Entitlements Report**: Exports all roles and their associated entitlements to `reports/all_roles_entitlements.csv`
- **Consolidated Excel Report**: Combines CSV files into a single Excel spreadsheet at `reports/reorg_entitlements_roles.xlsx` for easier analysis

## Logging

Logs are stored in the `logs` directory. Each script creates its own log file with detailed information about the execution, including any errors encountered during the process.

## Detailed Explanation

### api_connection.py

This file handles the connection to the SailPoint IdentityNow API. It includes functions to set up logging, load environment variables, and obtain an access token. The `get_api_connection` function creates the necessary headers for API requests, which include the access token for authentication.

### main.py

This script processes organizational changes and collects detailed information about identities:

- **CSV Processing**: Reads reorganization data from `reorg.csv`
- **Identity Retrieval**: Fetches identity details from SailPoint using the API
- **Role & Account Analysis**: Collects information about roles and accounts for each identity
- **Data Validation**: Verifies that department and team IDs match between the CSV and API data
- **Export**: Saves collected data to JSON and calls the export module to generate reports

### export.py

This module handles exporting identity data to various formats:

- **CSV Export**: Creates CSV files containing detailed information about entitlements and roles
- **Excel Export**: Combines CSV reports into a single Excel spreadsheet
- **Data Formatting**: Processes different types of entitlements based on their source system (Azure AD, Oracle, Active Directory)

## Use Cases

This tool is particularly useful during organizational restructuring by:

- Validating identity attributes before and after reorganization
- Identifying access inconsistencies between departments
- Analyzing role assignments across teams
- Providing documentation for audit and compliance purposes
- Supporting access reviews during transitions