import datetime
import json
import os
import subprocess
import time
import config
import pandas as pd
import requests
import utilities
from datetime import datetime, timedelta


def get_request(q):
    return requests.post(config.ENDPOINT, headers={"Authorization": "Bearer " + config.ACCESS_TOKEN},
                         json={"query": q}).json()

def is_token_valid():
    try:
        # Read the credentials file
        with open(config.credentials_file, 'r') as f:
            credentials = json.load(f)

        # Get the expiration time from the credentials (epoch time)
        expires_at = credentials.get('expires')

        if expires_at is None:
            print("Expiration time not found in credentials.")
            return False

        # Get the current time (epoch time)
        current_time = int(time.time())

        # Check if the token is still valid
        if current_time < expires_at:
            return True
        else:
            return False

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading credentials file: {e}")
        return False


def renew_token():
    try:
        # Run the instruqt auth login command to renew the token
        subprocess.run("instruqt auth login", shell=True, check=True)
        print("Token renewed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to renew token: {e}")


def check_and_renew_token():
    if is_token_valid():
        print("Token is still valid.")
    else:
        print("Token has expired or is invalid. Renewing token...")
        renew_token()


def send_slack_message():
    s = "This is an automated message to inform you that your Instruqt Hot start is not within guidelines. See the violations below: "

    return 0


def check_status(data):
    """Check if status is anything except 'Deleted' or 'Expired'."""
    status = data.get('status', '').lower()
    return status not in ['deleted', 'expired']


def check_dates(data):
    """Check if ends_at is None or if the difference between starts_at and ends_at is greater than 24 hours."""
    starts_at = data.get('starts_at')
    ends_at = data.get('ends_at')

    if not starts_at:
        return False, "starts_at is missing."

    starts_at_dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))

    if ends_at is None:
        return False, "End time is not set"

    ends_at_dt = datetime.fromisoformat(ends_at.replace('Z', '+00:00'))
    if abs((ends_at_dt - starts_at_dt).total_seconds()) > 24 * 3600:
        return False, "Pool TTL is greater than 24 hours"

    return True, None


def check_auto_refill(data):
    """Check if auto_refill is True."""
    auto_refill = data.get('auto_refill', False)
    if auto_refill:
        return False, "Auto fill is enabled"
    return True, None


def compile_message(data):
    """Compile messages based on date checks and auto_refill checks, excluding the status."""
    messages = []

    for node in data['data']['hotStartPools']['nodes']:
        node_messages = []
        node_name = node['name']

        # Check if the status requires further validation
        if check_status(node):
            # Check date validity
            dates_check, dates_message = check_dates(node)
            if not dates_check:
                node_messages.append(dates_message)

            # Check auto_refill
            auto_refill_check, auto_refill_message = check_auto_refill(node)
            if not auto_refill_check:
                node_messages.append(auto_refill_message)

        # Format the violations into a cohesive message
        if node_messages:
            email = node.get('created_by', {}).get('profile', {}).get('email', 'No email provided')
            message = f"This is an automated message to inform you that your Instruqt Hot start '{node_name}' is not within guidelines. See the violations below:\n\n"
            message += "\n".join(f"- {msg}" for msg in node_messages)
            message += f"\nCreated by: {email}\n" + "-" * 40
            messages.append(message)

    return "\n\n".join(messages)


def get_hotpool_violations():
    query = f"""query {{
                   hotStartPools(organizationSlug: "{config.ORG_SLUG}") {{
                    nodes {{
                        name
                        starts_at
                        ends_at
                        status
                        auto_refill
                        created_by {{
                            profile {{
                            email
                            }}
                        }}
                        }}
                   }}
               }}"""

    print(compile_message(get_request(query)))
