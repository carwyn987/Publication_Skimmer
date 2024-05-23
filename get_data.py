"""
Run syntax:
python main.py -k keyword1 keyword2 keyword3
"""

import json
import argparse
import pandas as pd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from src.querier import google_scholar_search

def main(keywords):
    print(f"Keywords: {keywords}")

    for keyword in keywords:
        print(f"Searching for: {keyword}")
        search_results = google_scholar_search(keyword)
        # df = pd.json_normalize(search_results, record_path=['resources'])
        print(search_results)


        # NEEDS FIXING!
        # df = pd.json_normalize(search_results[0], record_path=['publication_info.authors', 'resources'], meta=None, record_prefix=['Prefix_A.', 'Prefix_B.'])
        data = search_results[0]
        df1 = pd.json_normalize(data, 
                       record_path='publication_info', 
                       meta=['title', 'link', 'snippet'], 
                       record_prefix='Prefix_')

        df2 = pd.json_normalize(data, 
                            record_path='resources', 
                            meta=['title', 'link', 'snippet'], 
                            record_prefix='Prefix_')

        df = pd.concat([df1, df2], ignore_index=True)
        
        # df = pd.json_normalize(search_results[0], 
        #                     record_path='resources')

        # df = pd.concat([df1, df2], ignore_index=True)

        print(df)
        
        df.to_csv("data/" + f'{keyword.replace("+","").replace(" ","").strip()}.csv', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-k',
        '--keywords',
        nargs='+',
        type=str,
        help='One or more keywords (strings)'
    )

    args = parser.parse_args()
    keywords = args.keywords
    main(keywords)