import pandas as pd

def flatten_json(nested_json, exclude=[''], path=""):
    """Flatten json object with nested keys into a single level.
        Args:
            nested_json: A nested json object.
            exclude: Keys to exclude from output.
        Returns:
            The flattened json object if successful, None otherwise.
    """
    out = {}

    # print("NSJ: ", nested_json)

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

def load_one_record(json_data):
    # if 'resources' in json_data:
    #     df1 = pd.DataFrame([flatten_json(x, [""], "resources.") for x in json_data['resources']])
    # else:
    #     df1 = pd.DataFrame()
    # if 'authors' in json_data['publication_info']:
    #     df2 = pd.DataFrame([flatten_json(x, [""], "publication_info.authors.") for x in json_data['publication_info']['authors']])
    # else:
    #     df2 = pd.DataFrame()
    # df3 = pd.json_normalize(json_data)
    # df = pd.concat([df1, df2, df3], ignore_index=True)
    df = pd.DataFrame([flatten_json(json_data, [""], "")])
    return df

def load_all_records(json_data):
    dfs = []
    for data in json_data:
        dfs.append(load_one_record(data))
    return pd.concat(dfs, ignore_index=True)