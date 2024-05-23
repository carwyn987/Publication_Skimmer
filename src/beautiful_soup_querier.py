import requests
from bs4 import BeautifulSoup
import time
import random
import json

def google_scholar_search(query):

    results = []

    for start in sorted(list(range(0, 30, 10)), key=lambda x: random.random()):
        url = f"https://scholar.google.com/scholar?start={start}&q={query.replace(' ', '+')}&hl=en&as_sdt=0,3"
        user_agents = ['Mozilla/5.0', 'Chrome/56.0', 'Safari/10.1']
        headers = {'User-Agent': random.choice(user_agents)}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        res = soup.find_all('div', {'class': 'gs_ri'})

        for result in res:
            print(res)


            title = result.find('h3', {'class': 'gs_rt'}).text.replace("[PDF]","").replace("[HTML]","").replace("[BOOK]","").replace("[B]","").rstrip()
            author = result.find('div', {'class': 'gs_a'}).text.split("-")[0].strip().split(",")
            try:
                author_id = result.find('a', {'href': lambda x: x.startswith('/citations?user=')})['href'].split('=')[1]
            except:
                author_id = "NO_PROFILE_ID"
            description = result.find('div', {'class': 'gs_rs'}).text.strip()
            year = result.find('div', {'class': 'gs_a'}).text.split('-')[1].strip()
            # num_citations = result.find('a', {'href': lambda x: x.startswith('/scholar?cites=')}).text.split(' ')[1]
            num_citations = result.find('a', {'href': lambda x: x.startswith('/scholar?cites')}).text.strip().split(' ')[2]

            result_dict = {
                "Title": title,
                "Author": author,
                "Author ID": author_id,
                "Description": description,
                "Year": year,
                "Citations": num_citations
            }
            results.append(result_dict)
            # print(result_dict)
        
    print(len(results))
    return results

google_scholar_search("machine learning")