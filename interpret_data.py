import glob
import pandas as pd

if __name__ == "__main__":
    
    # Find all .csv files in the data folder
    csv_files = glob.glob('data/*.csv')

    # Initialize an empty list to store the DataFrames
    dfs = []

    # Load each .csv file into a DataFrame and append it to the list
    for file in csv_files:
        df = pd.read_csv(file)
        dfs.append(df)

    # Concatenate all the DataFrames into one big DataFrame
    df = pd.concat(dfs, ignore_index=True)

    # Print the first few rows of the DataFrame
    print("Combined DataFrame Head:")
    print(df.head())

    # Print the columns of the DataFrame
    print("Columns:")
    print(df.columns)

    # Print the summary statistics of the DataFrame
    print("Summary Statistics:")
    print(df.describe())