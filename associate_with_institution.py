import json
import requests
from tqdm import tqdm

def get_associations(author_name):
    # Google Custom Search API endpoint
    base_url = 'https://www.googleapis.com/customsearch/v1'

    with open('secret_sauce.json') as f: 
        GOOGLE_CUSTOMSEARCH_API_KEY = json.load(f)["GOOGLE_CUSTOMSEARCH_API_KEY"]
        SEARCH_ENGINE_ID = json.load(f)["SEARCH_ENGINE_ID"]
    
    # Search for the author using their name
    params = {
        'key': GOOGLE_CUSTOMSEARCH_API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': f"{author_name}"
    }
    
    associations = []  # Initialize a list to store affiliations

    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            search_results = response.json()
            items = search_results.get('items', [])
            for item in items:
                pagemap = item.get('pagemap', {})
                
                # Extract affiliation information
                hcard = pagemap.get('hcard', [])
                for card in hcard:
                    title = card.get('title')
                    if title:
                        associations.append(title)  # Add title from hcard
                
                person_list = pagemap.get('person', [])
                for person in person_list:
                    role = person.get('role')
                    org = person.get('org')
                    jobtitle = person.get('jobtitle')
                    worksfor = person.get('worksfor')
                    
                    if role:
                        associations.append(role)  # Add role from person
                    if org:
                        associations.append(org)  # Add organization from person
                    if jobtitle:
                        associations.append(jobtitle)  # Add job title from person
                    if worksfor:
                        associations.append(worksfor)  # Add works for from person

            return list(set(associations))  # Return unique affiliations
    except requests.RequestException as e:
        print(f"Error retrieving associations for {author_name}: {e}")
    
    return []  # Return an empty list if no affiliations found or on error


# Load the JSON data from the file
with open('data/author_info.json', 'r') as f:
    author_data = json.load(f)

# Iterate over the items and get affiliations with a progress bar
for key, value in tqdm(author_data.items(), desc="Fetching associations", unit="author"):
    try:
        author_id = value['author_ids'][0]  # Assuming you want the first ID in case of multiple
        associations = get_associations(author_id)
        value['associations'] = associations
        print("associations: ", associations)
    except Exception as e:
        print(f"Error processing author {key}: {e}")
        value['associations'] = []
# Create a list of tuples with author names and their data for sorting
reformatted_data = [(value['author'], {
    'citations': value['citations'],
    'titles': value['titles'],
    'associations': value['associations']
}) for value in author_data.values()]

# Debug: Print the reformatted data structure
print("Reformatted Data:", reformatted_data)

# Sort the reformatted data by citations (descending order)
sorted_data = sorted(reformatted_data, key=lambda item: item[1]['citations'], reverse=True)

# Debug: Print the sorted data structure
print("Sorted Data:", sorted_data)

# Create a final dictionary using sorted data
final_data = {author: data for author, data in sorted_data}

# Write the reformatted JSON back to a file
with open('data/reformatted_author_info.json', 'w') as f:
    json.dump(final_data, f, indent=4)

print("Reformatted JSON saved to data/reformatted_author_info.json")
