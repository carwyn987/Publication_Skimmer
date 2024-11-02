"""
Run syntax:
python get_data.py -k keyword1 keyword2 keyword3
"""

import json
import argparse
import pandas as pd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from src.querier import google_scholar_search
from src.ds_helper import load_one_record, load_all_records

def main(keywords, num_pages_to_query):
    # print(f"Keywords: {keywords}")

    for keyword in keywords:
        # print(f"Searching for: {keyword}")
        search_results = google_scholar_search(keyword, num_pages_to_query)
        # df = pd.json_normalize(search_results, record_path=['resources'])
        # print(search_results)

        data = search_results
        df = load_all_records(data)
        # print(df)
        # print("!!! ", df.columns)
        
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
    parser.add_argument(
        '-n',
        '--num-pages-to-query',
        type=int,
        default=3,
        help='Number of pages to query (default: 3)'     
    )

    args = parser.parse_args()
    keywords = args.keywords
    num_pages_to_query = args.num_pages_to_query
    main(keywords, num_pages_to_query)