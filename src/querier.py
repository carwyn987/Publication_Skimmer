import requests
from bs4 import BeautifulSoup
import time
import random
import json

def google_scholar_search(query):

    with open('secret_sauce.json') as f: 
        api_key = json.load(f)["api_key"]

    results = []

    # Iterate over 3 pages of Google Scholar search results. Randomization is used to avoid getting blocked.
    # for start in sorted(list(range(0, 40, 20)), key=lambda x: random.random()):
    for start in range(0, 100, 20):
        params = {
            "q": query,
            "hl": "en",
            "start": start,
            "num": 20, # maximum
            "api_key": api_key,
            "engine":"google_scholar"
        }

        response = requests.get("https://serpapi.com/search", params=params)
        res = response.json()
        if res["search_metadata"]["status"] != "Success":
                print("Error")
                continue
        res = res["organic_results"]

        for result in res:

            # result_dict = {
            #     "Title": result["title"],
            #     "Author": ', '.join(author["name"] for author in result["publication_info"]["authors"]),
            #     "Author ID": ', '.join(author["author_id"] for author in result["publication_info"]["authors"]),
            #     "Description": result["snippet"],
            #     "Year": result["publication_info"]["summary"].split(" - ")[1],
            #     "Citations": result["inline_links"]["cited_by"]["total"]
            # }

            results.append(result)
            # print(result_dict)
        
    print(len(results))
    return results

google_scholar_search("machine learning")