
import json 
import pandas as pd
import sys
sys.path.append('/home/carwyn/development/publication_skimmer/src')
from ds_helper import load_one_record, load_all_records


f = open('data/example_serpapi_all.json','r')
data = json.load(f)

df = load_all_records(data)

print(df.head())
print(df.columns)