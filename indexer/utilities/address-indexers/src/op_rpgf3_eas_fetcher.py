import json
import os
import pandas as pd
import requests
from urllib.parse import urlparse


from ossd import get_yaml_data_from_path, map_addresses_to_slugs, map_repos_to_slugs


ATTESTATIONS = {
    "Optimist Profile": "0xac4c92fc5c7babed88f78a917cdbcdc1c496a8f4ab2d5b2ec29402736b2cf929",
    "RPGF3 Application": "0x76e98cce95f3ba992c2ee25cef25f756495147608a3da3aa2e5ca43109fe77cc",
}

JSON_ATTESTATION_DATA = "data/rpgf3/indexed_attestations.json"
JSON_APPLICANT_DATA = "data/rpgf3/applicant_data.json"
CSV_OUTPUT_PATH = "data/rpgf3/applicant_data.csv"
MATCHED_APPLICANT_DATA = "data/rpgf3/matched_applicant_data.json"


def fetch_attestations_for_schema(schema_id, schema_name, time_created_after=0):
    url = 'https://optimism.easscan.org/graphql'
    query_limit = 100 
    query = '''
    query Attestations($schemaId: StringFilter!, $skip: Int!, $take: Int!, $timeCreatedAfter: IntFilter) {
    attestations(where: {schemaId: $schemaId, timeCreated: $timeCreatedAfter}, take: $take, skip: $skip) {
        id
        attester
        recipient
        refUID
        revocable
        revocationTime
        expirationTime
        timeCreated 
        decodedDataJson    
    }
    }
    '''
    
    variables = {
        "schemaId": {
            "equals": schema_id
        },
        "skip": 0,
        "take": query_limit,
        "timeCreatedAfter": {"gt": time_created_after},
    }

    headers = {
        'Content-Type': 'application/json',
    }

    all_attestations = []

    while True:
        payload = {
            'query': query,
            'variables': variables
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            try:
                data = response.json()
                if 'data' in data and 'attestations' in data['data']:
                    attestations = data['data']['attestations']
                    if attestations is None:
                        break
                    all_attestations.extend(attestations)
                else:
                    print(f"Unexpected response structure: {data}")
                    break

                if len(attestations) < query_limit:
                    break

                variables["skip"] += query_limit
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {str(e)}")
                break
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            break

    print(f"Total attestations for {schema_name}: {len(all_attestations)}")
    return all_attestations


def fetch_json_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch JSON data from URL: {url}")
            return None
    except Exception as e:
        print(f"Error fetching JSON data from URL: {url}. Error: {str(e)}")
        return None


def fetch_and_update_json_data(data_entry):
    for data_item in data_entry:
        value = data_item.get("value", {}).get("value", {})
        if isinstance(value, str) and ".json" in value:
            json_data = fetch_json_data(value)
            if json_data:
                data_item.update({"json_data": json_data})


def update_json_file(schema_name_to_index):

    existing_data = []
    last_time_created = 0
    if os.path.exists(JSON_ATTESTATION_DATA):
        with open(JSON_ATTESTATION_DATA, "r") as json_file:
            existing_data = json.load(json_file)
        last_time_created = max([a["timeCreated"] for a in existing_data])

    indexed_data = []

    if schema_name_to_index in ATTESTATIONS:
        schema_id = ATTESTATIONS[schema_name_to_index]
        schema_attestations = fetch_attestations_for_schema(schema_id, schema_name_to_index, time_created_after=last_time_created)

        for a in schema_attestations:
            decoded_data = json.loads(a["decodedDataJson"])
            fetch_and_update_json_data(decoded_data)
            indexed_data.append({
                "id": a["id"],
                "attester": a["attester"],
                "timeCreated": a["timeCreated"],
                "data": decoded_data
            })
    
    existing_data.extend(indexed_data)
    
    with open(JSON_ATTESTATION_DATA, "w") as json_file:
        json.dump(existing_data, json_file, indent=4)


# very brittle, but works for now
def clean_data(original_data):

    project_name = original_data["data"][0]["value"]["value"]
    project_link = original_data["data"][2]["value"]["value"]
    json_data = original_data["data"][2].get("json_data", None)
    if json_data is None:
        print(f"No JSON data found for {project_name} at {project_link}.")
        return None

    transformed_data = {
        "Project Name": project_name,  # Extract "displayName"
        "Applicant Type": json_data["applicantType"],  # Extract "applicantType" from "applicationMetadataPtr"
        "Date": original_data["timeCreated"],  # Extract "timeCreated"
        "Attester Address": original_data["attester"],  # Extract "attester"
        "Payout Address": json_data["payoutAddress"],  # Extract "payoutAddress" from "applicationMetadataPtr"
        "Link": project_link,  # Extract "applicationMetadataPtr"
        "Tags": json_data["impactCategory"],  # Extract "impactCategory" from "applicationMetadataPtr"
        "Github Urls": [item["url"] for item in json_data["contributionLinks"] if item["type"] == "GITHUB_REPO"]  # Extract "GITHUB_REPO" URLs from "contributionLinks" in "applicationMetadataPtr"
    }
    return transformed_data


def check_for_ossd_membership(cleaned_data):

    yaml_data = get_yaml_data_from_path()

    addresses_to_slugs = map_addresses_to_slugs(yaml_data, "optimism", lowercase=True)
    address_set = set(addresses_to_slugs.keys())

    get_owner = lambda url: urlparse(url).path.split('/')[1].lower() if 'github.com' in url else None

    repos_to_slugs = map_repos_to_slugs(yaml_data, lowercase=True)
    repo_owners_to_slugs = {}
    for repo, slug in repos_to_slugs.items():
        owner = get_owner(repo)
        if owner is None:
            continue
        if owner not in repo_owners_to_slugs:
            repo_owners_to_slugs[owner] = set()
        repo_owners_to_slugs[owner].add(slug)
    repo_owner_set = set(repo_owners_to_slugs.keys())

    ossd_mappings = {}    
    for entry in cleaned_data:        
        
        possible_slugs = []

        address_verified = False
        if entry["Payout Address"].lower() in address_set:
            address_verified = True
            possible_slugs = [addresses_to_slugs[entry["Payout Address"].lower()]]
        if entry["Attester Address"].lower() in address_set:
            address_verified = True
            possible_slugs = [addresses_to_slugs[entry["Attester Address"].lower()]]
        
        github_verified = False
        github_owners = set([get_owner(repo) for repo in entry['Github Urls'].split(", ")])
        if None in github_owners:
            github_owners.remove(None)
        matching_owners = github_owners.intersection(repo_owner_set)
        if matching_owners:
            github_verified = True
            if not address_verified:
                possible_slugs = [slug for owner in matching_owners for slug in repo_owners_to_slugs[owner]]
            
        if github_verified and address_verified:
            entry["OSS Directory"] = "Address & Github Found"
        elif github_verified:
            entry["OSS Directory"] = "Github Found"
        elif address_verified:
            entry["OSS Directory"] = "Address Found"
        else:
            entry["OSS Directory"] = "Not Found"
            continue
        
        if len(possible_slugs) == 1:
            entry["Slug(s)"] = possible_slugs[0]
        elif len(possible_slugs) > 1:
            entry["Slug(s)"] = ", ".join(possible_slugs)


def clean_applicant_data():
    with open(JSON_ATTESTATION_DATA, "r") as json_file:
        original_data = json.load(json_file)
    cleaned_data = [clean_data(data) for data in original_data]
    cleaned_data = [data for data in cleaned_data if data is not None]
    with open(JSON_APPLICANT_DATA, "w") as json_file:
        json.dump(cleaned_data, json_file, indent=4)
    
    for entry in cleaned_data:
        entry["Tags"] = ", ".join(entry["Tags"])
        entry["Github Urls"] = ", ".join(entry["Github Urls"])
        entry["OSS Directory"] = "Unknown"

    check_for_ossd_membership(cleaned_data)

    matched_data = [data for data in cleaned_data if data["OSS Directory"] != "Not Found"]
    with open(MATCHED_APPLICANT_DATA, "w") as json_file:
        json.dump(matched_data, json_file, indent=4)

    csv_data = pd.DataFrame(cleaned_data)
    fieldnames = ["Project Name", "Applicant Type", "Date", "Attester Address", "Payout Address", "Link", "Tags", "Github Urls", "OSS Directory"]
    csv_data = csv_data[fieldnames]
    csv_data.sort_values(by="Date", inplace=True)
    csv_data.drop_duplicates(subset=["Link"], keep="last", inplace=True)
    csv_data.to_csv(CSV_OUTPUT_PATH, index=False)


def main():
    update_json_file("RPGF3 Application")
    clean_applicant_data()


if __name__ == "__main__":
    main()