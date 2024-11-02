import glob
import json
import pandas as pd
from collections import OrderedDict

if __name__ == "__main__":
    
    # Find all .csv files in the data folder
    csv_files = glob.glob('data/*.csv')
    # exclude author_info.csv
    csv_files = [file for file in csv_files if 'author_info' not in file]
    # exclude example_outs/ folder
    csv_files = [file for file in csv_files if 'example_outs' not in file]

    # Initialize an empty list to store the DataFrames
    dfs = []

    # Load each .csv file into a DataFrame and append it to the list
    for file in csv_files:
        df = pd.read_csv(file)
        dfs.append(df)

    # Concatenate all the DataFrames into one big DataFrame
    df = pd.concat(dfs, ignore_index=True)

    # Create an empty dictionary to store the author information
    author_dict = {}

    # Iterate over df rows:
    for index, row in df.iterrows():
        authors = []

        publication_info_summary = row['publication_info_summary']
        # Extract the authors from the publication_info_summary
        authors_text = publication_info_summary.split('-')[0].strip()
        # Split the authors by comma and remove any leading/trailing spaces
        authors_list = [author.strip().replace("…", "").replace("...", "") for author in authors_text.split(',')]
        # Add the authors to the authors list
        authors.extend(authors_list)
        
        # Iterate through the authors columns
        for i in range(10):  # Assuming there are 10 authors
            author_name_col = f'publication_info_authors_{i}_name'
            author_id_col = f'publication_info_authors_{i}_author_id'
            
            if author_name_col in row and pd.notna(row[author_name_col]):
                author_name = row[author_name_col]
                authors.append(author_name)

                # Get the corresponding author ID
                if author_id_col in row and pd.notna(row[author_id_col]):
                    author_id = row[author_id_col]
                else:
                    author_id = None  # No ID available

                # Initialize or update the author entry
                if author_name not in author_dict:
                    author_dict[author_name] = {'citations': 0, 'titles': [], 'author_ids': []}
                
                if author_id and author_id not in author_dict[author_name]['author_ids']:
                    author_dict[author_name]['author_ids'].append(author_id)

        # Get number of citations
        citations = row['inline_links_cited_by_total']  # can be nan
        # Get the title of the publication
        title = row['title']
        
        # Update the author information in the dictionary
        for author in authors:
            if author not in author_dict:
                author_dict[author] = {'citations': 0, 'titles': [], 'author_ids': []}
            if citations is not None and not pd.isna(citations):
                author_dict[author]['citations'] += citations
            if title is not None and not pd.isna(title):
                author_dict[author]['titles'].append(title)

    # Create a new dictionary to store the sorted author information
    sorted_author_dict = OrderedDict()

    # Sort the authors based on the number of citations in descending order
    sorted_authors = sorted(author_dict.keys(), key=lambda x: author_dict[x]['citations'], reverse=True)

    # Populate the sorted_author_dict with the sorted author information
    for index, author in enumerate(sorted_authors):
        sorted_author_dict[index + 1] = {
            'author': author,
            'citations': author_dict[author]['citations'],
            'titles': author_dict[author]['titles'],
            'author_ids': author_dict[author]['author_ids']
        }

    # Save the sorted_author_dict to a JSON file
    with open('data/author_info.json', 'w') as f:
        json.dump(dict(sorted_author_dict), f, indent=4)

    # Save the json file as a csv, with columns of "author", "citations", "titles", and "author_ids"
    author_df = pd.DataFrame(sorted_author_dict).T
    author_df.to_csv('data/author_info.csv', index=False)
