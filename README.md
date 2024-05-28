# Brainstorming

I have a bunch of keywords for topics I want to research in university
 - Reinforcement Learning
 - AIXI

What I need is a list of professors with publications in these areas, and their associated universities. I also want some summary statistics, including top universities and professors by aggregate count.

How can I build a tool (with python) to do this? Or does a tool already exist?

https://www.youtube.com/watch?v=ppGRPWpv9Wc 

Query online and get:
 - author name
 - university or affiliated association
 - citations
 - article / publication title
 - keywords

Query either
 - Semantic scholar
 - Google scholar https://serpapi.com/google-scholar-api 



Let's make this simple
 - Data storage = Pandas dataframe
 - querying with BeautifulSoup

# To use this tool

```get_data.py``` queries google scholar for articles given a keyword.
```interpret_data.py``` Takes that data, computes citations and publications by author, and saves in ```data/author_info.json``` file.

#### Set up SERP API key

Querying with beautiful soup and the requests library will quickly be blocked due to chrome TOS. Therefore, I used SERP api. Create a free account, and then create a file called ```secret_sauce.json``` in the base directory, and fill it with:

```
{
    "api_key": "YOUR_API_KEY"
}
```

## Query data

Run ```get_data``` with keywords and advanced search queries like the following:

```
python get_data.py -k '"reinforcement learning" AND ("aixi" OR "dqn" OR "induction" OR "solomonoff" OR "kolmogorov" OR "knowledge graph")'
```

A file will be generated in the ```data/``` folder with the same name as the ```-k``` option.

## Interpret data

Modify the path in the ```interpret_data.py``` file.

Run ```python interpret_data.py``` to generate the ```author_info.json``` and ```author_info.csv``` data file, sorted by publications. For me, this makes it easy to scroll through and find relevant and contributing professors and figures in industry.