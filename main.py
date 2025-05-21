import os
import csv
import json
import requests
import logging
from dotenv import load_dotenv
from api_connection import get_api_connection
from export import export_data  

# Function to set up logging
def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logger = logging.getLogger('reorgs')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('logs/reorgs.log')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Set up logging
logger = setup_logging()
logger.info("Logging setup complete.")

# Load environment variables from a .env file
load_dotenv(override=True)
cert_path = os.getenv("CERT_PATH")
base_url = os.getenv('BASE_URL')
identities_url = f"{base_url}beta/identities"
headers = get_api_connection()

# Ensure all required environment variables are set
if not all([base_url, cert_path]):
    logger.error("Missing one or more required environment variables.")
    raise EnvironmentError("Missing one or more required environment variables.")

# Function to get identity by alias
def get_identity_by_alias(alias):
    filters = f"alias eq \"{alias}\""
    try:
        response = requests.get(f"{identities_url}?filters={filters}", headers=headers, verify=cert_path)
        if response.status_code == 200:
            identities = response.json()
            if identities:
                return identities[0]
            else:
                logger.info(f"No matching identity found for alias: {alias}")
                return None
        else:
            logger.error(f"Failed to retrieve identities for alias: {alias}. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception occurred while retrieving identities for alias: {alias}. Error: {e}")
        return None

# Function to get role assignments by identity ID
def get_role_assignments(identity_id):
    role_assignments_url = f"{base_url}beta/identities/{identity_id}/role-assignments"
    try:
        response = requests.get(role_assignments_url, headers=headers, verify=cert_path)
        if response.status_code == 200:
            role_assignments = response.json()
            roles = [{"name": role_assignment['role']['name'], "owner": role_assignment['role'].get('owner', {}).get('name', 'N/A'), "entitlements": {}, "id": role_assignment['role']['id']} for role_assignment in role_assignments]
            return roles
        else:
            logger.error(f"Failed to retrieve role assignments for identity ID: {identity_id}. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception occurred while retrieving role assignments for identity ID: {identity_id}. Error: {e}")
        return []

# Function to get role details by role ID
def get_role_details(role_id):
    role_details_url = f"{base_url}beta/roles/{role_id}"
    try:
        response = requests.get(role_details_url, headers=headers, verify=cert_path)
        if response.status_code == 200:
            role_details = response.json()
            entitlements = role_details.get("entitlements", [])
            parsed_entitlements = [{"id": ent["id"], "name": ent["name"]} for ent in entitlements]
            return {
                "name": role_details["name"],
                "owner": role_details.get("owner", {}).get("name", "N/A"),
                "entitlements": parsed_entitlements
            }
        else:
            logger.error(f"Failed to retrieve role details for role ID: {role_id}. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception occurred while retrieving role details for role ID: {role_id}. Error: {e}")
        return {}

# Function to get accounts by identity ID
def get_accounts(identity_id):
    accounts_url = f"{base_url}beta/accounts?filters=identityId eq \"{identity_id}\""
    try:
        response = requests.get(accounts_url, headers=headers, verify=cert_path)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to retrieve accounts for identity ID: {identity_id}. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception occurred while retrieving accounts for identity ID: {identity_id}. Error: {e}")
        return []

# Function to get entitlements by account ID
def get_entitlements(account_id, source_name):
    entitlements_url = f"{base_url}beta/accounts/{account_id}/entitlements"
    try:
        response = requests.get(entitlements_url, headers=headers, verify=cert_path)
        if response.status_code == 200:
            entitlements = response.json()
            parsed_entitlements = []
            for entitlement in entitlements:
                if source_name == "Azure Active Directory":
                    if entitlement["attribute"] == "appRoleAssignments":
                        parsed_entitlements.append({
                            "attribute": "AppRoleAssignment",
                            "displayName": entitlement["attributes"].get("displayName", "No displayName"),
                            "appRole_description": entitlement["attributes"].get("appRole_description", "No description")
                        })
                    elif entitlement["attribute"] == "azureADEligibleRoles":
                        parsed_entitlements.append({
                            "attribute": "azureADEligibleRoles",
                            "roleName": entitlement["attributes"]["roleName"]
                        })
                elif source_name == "Oracle | Multi Applications":
                    if entitlement["attribute"] == "APP_ROLE_CODE":
                        parsed_entitlements.append({
                            "attribute": "APP_ROLE_CODE",
                            "APP_ROLE_NAME": entitlement["attributes"]["APP_ROLE_NAME"]
                        })
                else:
                    parsed_entitlements.append({
                        "value": entitlement["value"],
                        "description": entitlement.get("description", "no description")
                    })
            return parsed_entitlements
        else:
            logger.error(f"Failed to retrieve entitlements for account ID: {account_id}. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception occurred while retrieving entitlements for account ID: {account_id}. Error: {e}")
        return []

# Function to process reorg.csv
def process_reorg_csv():
    identities = []
    role_cache = {}

    with open('reorg.csv', mode='r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        headers = next(csv_reader)  # Extract headers
        print(f'Column names are: {", ".join(headers)}')
        
        for row in csv_reader:
            payroll_id = row[0].strip()
            current_department_id = row[3].strip()
            new_department_id = row[4].strip()
            current_team_id = row[5].strip()
            new_team_id = row[6].strip()

            identity = get_identity_by_alias(payroll_id)
            if identity:
                identity_id = identity['id']
                identity_department_id = identity['attributes'].get('departmentId')
                identity_team_id = identity['attributes'].get('teamId')

                # Fetch role assignments and add to identity details
                roles = get_role_assignments(identity_id)
                for role in roles:
                    role_id = role['id']
                    if role_id not in role_cache:
                        role_cache[role_id] = get_role_details(role_id)
                    role['details'] = role_cache[role_id]
                identity['roles'] = roles

                # Fetch accounts and entitlements
                accounts = get_accounts(identity_id)
                simplified_accounts = []
                for account in accounts:
                    account_id = account['id']
                    source_name = account['sourceName']
                    entitlements = get_entitlements(account_id, source_name)
                    simplified_account = {
                        "sourceName": source_name,
                        "entitlements": entitlements
                    }
                    simplified_accounts.append(simplified_account)
                identity['accounts'] = simplified_accounts

                if identity_department_id != current_department_id or identity_team_id != current_team_id:
                    logger.error(f"Mismatch for alias {payroll_id}: CSV departmentId={current_department_id}, API departmentId={identity_department_id}; CSV teamId={current_team_id}, API teamId={identity_team_id}")
                else:
                    logger.info(f"Match for alias {payroll_id}: departmentId and teamId are correct.")

                identities.append(identity)

    # Save all identities' details to a single file
    with open('all_identities.json', 'w') as f:
        json.dump(identities, f, indent=4)
    
    # Call the export function with the collected data
    logger.info("Starting export process...")
    export_data(identities)
    logger.info("Export process completed.")

if __name__ == "__main__":
    process_reorg_csv()