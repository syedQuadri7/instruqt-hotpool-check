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


def get_track_plays_by_month(track_slugs, org_slug=config.ORG_SLUG, filter_developers=config.FILTER_DEVELOPERS,
                             dates=utilities.month_map(config.YEAR)):
    slug_data = []
    for track_slug in track_slugs:
        print(track_slug)
        row = []
        for k, v in dates.items():
            query = f"""
                query {{
                    statistics(trackSlug: "{track_slug}", organizationSlug: "{org_slug}", filterDevelopers: {filter_developers}, start: "{k}", end: "{v}") {{
                        track {{
                            title
                            started_total
                        }}
                    }}
                }}
            """

            track = get_request(query)

            title = track["data"]["statistics"]["track"]["title"]
            started_total = track["data"]["statistics"]["track"]["started_total"]
            if title not in row:
                row.append(title)
            row.append(started_total)

        slug_data.append(row)
    return create_table(slug_data)

def get_track_slugs():
    query = f"""query {{
           tracks(organizationSlug: "{config.ORG_SLUG}") {{
             slug
           }}
       }}"""

    output = get_request(query)
    print(output)
    slugs = [track['slug'] for track in output.json()['data']['tracks']]
    return slugs


def create_table(data, file_type='csv', file_name='tracks_by_month'):
    # Define the months as the column headers
    months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']

    # Extract the topics and values from the data
    topics = [item[0] for item in data]
    values = [item[1:] for item in data]

    # Create the DataFrame with topics as the index and months as the columns
    df = pd.DataFrame(values, index=topics, columns=months)

    file_path = f'outputs/{file_name}.csv'
    df.to_csv(file_path)

    print(f"Data has been saved to {file_path}")


def get_tracks_scores(file_name='track_scores'):
    query = f"""query {{
               tracks(organizationSlug: "{config.ORG_SLUG}") {{
                 slug
                 statistics {{
                    title
                    started_total
                    completed_total
                    average_review_score
                    }}
               }}
           }}"""

    data = get_request(query)

    # Initialize an empty list to hold the data for each track
    d = []

    # Iterate over the tracks in the JSON data
    for track in data['data']['tracks']:
        # Extract relevant statistics
        title = track['statistics']['title']
        started = track['statistics']['started_total']
        completed = track['statistics']['completed_total']
        average_review_score = track['statistics']['average_review_score']

        # Calculate percent completed and round to 2 decimal places
        percent_completed = round((completed / started * 100), 2) if started > 0 else 0.00

        # Round average_review_score to 2 decimal places, but only if it's not None
        if average_review_score is not None:
            average_review_score = round(average_review_score, 2)

        # Append the row to the data list
        d.append({
            'Title': title,
            'Started': started,
            'Completed': completed,
            'Percent Completed': percent_completed,
            'Average Review Score': average_review_score
        })

    # Create a DataFrame from the data list
    df = pd.DataFrame(d)

    # Write the DataFrame to a CSV file
    file_path = f'outputs/{file_name}.csv'
    df.to_csv(file_path, index=False)

def get_slugs_with_tag(tag_val):
    query = f"""query {{
               tracks(organizationSlug: "{config.ORG_SLUG}") {{
                slug
                title
                 trackTags {{
                    value
                 }}
               }}
           }}"""

    data = (get_request(query))

    tagged_slugs = []
    tagged_titles = []
    for track in data.get('data', {}).get('tracks', []):
        for tag in track.get('trackTags', []):
            if tag.get('value') == tag_val:
                tagged_slugs.append(track.get('slug'))
                tagged_titles.append(track.get('title'))
                break

    write_list_to_file(tagged_titles, tag_val)
    return tagged_slugs


def write_list_to_file(lines, name):
    name = f"outputs/{name}_tag_output.txt"
    with open(name, 'w') as f:
        for line in lines:
            f.write(f"{line}\n")


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
