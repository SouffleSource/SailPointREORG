# Import necessary libraries
import os
import requests
import logging
from dotenv import load_dotenv

# Function to set up logging
def setup_logging():
    # Check if 'logs' directory exists, if not, create it
    if not os.path.exists('logs'):
       os.makedirs('logs')
    # Create a logger object
    logger = logging.getLogger('api_connection')
    # Set the logging level to INFO
    logger.setLevel(logging.INFO)
    # Create a file handler to write log messages to a file
    handler = logging.FileHandler('logs/api_connection.log')
    # Define the format for the log messages
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    # Set the formatter for the handler
    handler.setFormatter(formatter)
    # Add the handler to the logger
    logger.addHandler(handler)
    # Return the logger object
    return logger

# Set up logging and store the logger object in a variable
logger = setup_logging()
# Log a message indicating that logging setup is complete
logger.info("Logging setup complete.")

# Load environment variables from a .env file
load_dotenv()
# Get the values of the environment variables and set them as strings so they can be used in the script
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
cert_path = os.getenv("CERT_PATH")
base_url = os.getenv('BASE_URL')
# Construct the authentication URL using the base URL string
auth_url = f"{base_url}oauth/token"

# Function to check if all required environment variables are set
if not all([client_id, client_secret, cert_path, base_url]):
    # Log an error message if any environment variable is missing
    logger.error("Missing one or more required environment variables.")
    # Raise an error to stop the program
    raise EnvironmentError("Missing one or more required environment variables.")

# Function to get an access token from the API
def get_access_token():
    # Data to be sent in the POST request to get the access token
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }
    try:
        # Send a POST request to the authentication URL with the data
        response = requests.post(auth_url, data=data, verify=cert_path)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Log a success message
            logger.info("Successfully obtained access token.")
            # Return the access token from the response
            return response.json().get('access_token')
        else:
            # Log an error message if the request failed
            logger.error(f"Failed to obtain access token. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        # Log an error message if an exception occurred during the request
        logger.error(f"Exception occurred while obtaining access token: {e}")
        return None

# Function to create the API connection headers, which contain the access token
def get_api_connection():
    # Get the access token
    access_token = get_access_token()
    # Check if the access token was obtained successfully
    if access_token:
        # Create the headers for the API connection
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f"Bearer {access_token}",
        }
        # Log a success message
        logger.info("Successfully created API connection headers.")
        # Return the headers
        return headers
    else:
        # Log an error message if the access token was not obtained
        logger.error("Failed to obtain access token.")
        # Raise an error to indicate the failure
        raise ConnectionError("Failed to obtain access token.")