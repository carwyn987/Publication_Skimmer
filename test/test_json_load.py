import json 
import pandas as pd

f = open('data/example_serpapi_out.json','r')
data = json.load(f)


def flatten_json(nested_json, exclude=[''], path=""):
    """Flatten json object with nested keys into a single level.
        Args:
            nested_json: A nested json object.
            exclude: Keys to exclude from output.
        Returns:
            The flattened json object if successful, None otherwise.
    """
    out = {}

    def flatten(x, name='', exclude=exclude, path=path):
        if type(x) is dict:
            for a in x:
                if a not in exclude: flatten(x[a], path + name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, path + name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out

df1 = pd.DataFrame([flatten_json(x, [""], "resources.") for x in data['resources']])
df2 = pd.DataFrame([flatten_json(x, [""], "publication_info.authors.") for x in data['publication_info']['authors']])
df3 = pd.json_normalize(data)

df = pd.concat([df1, df2, df3], ignore_index=True)
print(df.head())
print(df.columns)