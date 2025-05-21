import os
import csv
import json
import logging
import pandas as pd

# Function to set up logging
def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logger = logging.getLogger('export')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('logs/export.log')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Set up logging
logger = setup_logging()
logger.info("Logging setup complete.")

# Load identities from JSON file
def load_identities(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)

# Function to extract CN value
def extract_cn(value):
    if value.startswith("CN="):
        return value.split(",")[0][3:]
    return value

# Function to check if entitlement is part of a role and return the role name
def get_role_name_for_entitlement(identity, entitlement_name):
    for role in identity.get('roles', []):
        entitlements = role.get('details', {}).get('entitlements', [])
        for entitlement in entitlements:
            if entitlement['name'] == entitlement_name:
                return role['name']
    return ""

# Function to write entitlements to a single CSV
def write_entitlements_to_csv(identities):
    if not os.path.exists('reports'):
        os.makedirs('reports')
    csv_file = "reports/all_identities_entitlements.csv"
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["identityName", "sourceName", "entitlementValue", "description", "part of role"])

        for identity in identities:
            display_name = identity.get('name', 'unknown_identity').replace(" ", "_")
            for account in identity.get('accounts', []):
                source_name = account['sourceName']
                for entitlement in account.get('entitlements', []):
                    if source_name == "Azure Active Directory":
                        if entitlement["attribute"] == "AppRoleAssignment":
                            entitlement_name = entitlement["displayName"]
                        elif entitlement["attribute"] == "azureADEligibleRoles":
                            entitlement_name = entitlement["roleName"]
                    elif source_name == "Oracle | Multi Applications":
                        entitlement_name = entitlement["APP_ROLE_NAME"]
                    elif source_name in ["Active Directory | Production", "Active Directory"]:
                        entitlement_name = extract_cn(entitlement["value"])
                    elif source_name == "Oracle | Legacy Accounts":
                        entitlement_name = entitlement["value"]
                    else:
                        entitlement_name = entitlement.get("name", entitlement.get("roleName", entitlement.get("value", "")))

                    role_name = get_role_name_for_entitlement(identity, entitlement_name)
                    part_of_role = role_name if role_name else ""

                    if source_name == "Azure Active Directory":
                        if entitlement["attribute"] == "AppRoleAssignment":
                            writer.writerow([display_name, source_name, entitlement["displayName"], entitlement.get("description", ""), part_of_role])
                        elif entitlement["attribute"] == "azureADEligibleRoles":
                            writer.writerow([display_name, source_name, entitlement["roleName"], entitlement.get("description", ""), part_of_role])
                    elif source_name == "Oracle | Multi Applications":
                        if entitlement["attribute"] == "APP_ROLE_CODE":
                            writer.writerow([display_name, source_name, entitlement["APP_ROLE_NAME"], entitlement.get("description", ""), part_of_role])
                    elif source_name in ["Active Directory | Production", "Active Directory"]:
                        writer.writerow([display_name, source_name, entitlement_name, entitlement.get("description", ""), part_of_role])
                    elif source_name == "Oracle | Legacy Accounts":
                        writer.writerow([display_name, source_name, entitlement["value"], entitlement.get("description", ""), part_of_role])

    logger.info(f"Exported all entitlements to {csv_file}")

# Function to write roles to CSV
def write_roles_to_csv(identities):
    unique_roles = {}
    for identity in identities:
        display_name = identity.get('name', 'unknown_identity')
        for role in identity.get('roles', []):
            role_name = role['name']
            entitlements = role.get('details', {}).get('entitlements', [])
            for entitlement in entitlements:
                entitlement_name = entitlement['name']
                if role_name not in unique_roles:
                    unique_roles[role_name] = {}
                if entitlement_name not in unique_roles[role_name]:
                    unique_roles[role_name][entitlement_name] = set()
                unique_roles[role_name][entitlement_name].add(display_name)

    if not os.path.exists('reports'):
        os.makedirs('reports')
        
    csv_file = "reports/all_roles_entitlements.csv"
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["roleName", "entitlementName", "identities"])
        for role_name, entitlements in unique_roles.items():
            for entitlement_name, identities in entitlements.items():
                writer.writerow([role_name, entitlement_name, ", ".join(identities)])

    logger.info(f"Exported all unique roles and entitlements to {csv_file}")

# Function to combine CSV files into an Excel spreadsheet
def combine_csv_to_excel():
    excel_file = "reports/reorg_entitlements_roles.xlsx"
    with pd.ExcelWriter(excel_file) as writer:
        for csv_file in os.listdir('reports'):
            if csv_file.endswith('.csv'):
                df = pd.read_csv(f'reports/{csv_file}')
                sheet_name = os.path.splitext(csv_file)[0]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    logger.info(f"Combined all CSV files into {excel_file}")

# Main function to process identities and export entitlements and roles
# Renamed from export_entitlements_and_roles to export_data to match import in main.py
def export_data(identities):
    write_entitlements_to_csv(identities)
    write_roles_to_csv(identities)
    combine_csv_to_excel()

if __name__ == "__main__":
    export_data(load_identities('all_identities.json'))