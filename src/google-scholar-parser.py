# CREDIT TO https://github.com/merenlab/google-scholar-parser/tree/main
# CREDIT TO @danuccio, @meren : meren A. Murat Eren (Meren) 
# NONE OF THIS CODE IS MINE

#!/usr/bin/env python3.9
#-*-coding: utf-8

###Imports
import io
import os
import re
import sys
import csv
import time
import pathlib
import urllib3
import argparse

from contextlib import redirect_stderr

from random import *

###More Imports
import json
import requests
import urllib.parse
from urllib.error import HTTPError
from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen, Request

# try to import scholarly to make sure it is installed
try:
    import scholarly
except ImportError:
    print("You need the Python module 'scholarly' to be installed on your system for this program to work. Try running this in your terminal: 'pip install scholarly==1.4.5'.")
    sys.exit()

from scholarly import scholarly

try:
    from scholarly import DOSException
    from scholarly import MaxTriesExceededException
    from scholarly import ProxyGenerator #Necessary for using ScraperAPI
except ImportError:
    print("You have the wrong version of scholarly :/ Try running this in your terminal: 'pip install --upgrade scholarly==1.4.5'.")
    sys.exit()

try:
    import habanero
except ImportError:
    print("You need the Python module 'habanero' to be installed on your system for this program to work. Try running this in your terminal: 'pip install habanero==1.0.0'.")
    sys.exit()

try:
    from habanero import Crossref
except ImportError:
    print("You have the wrong version of habanero :/ Try running this in your terminal: 'pip install --upgrade habanero==1.0.0'.")
    sys.exit()

try:
    import Levenshtein
except ImportError:
    print("You need the Python module 'Levenshtein' to be installed on your system for this program to work. Try running this in your terminal: 'pip install Levenshtein==0.16.0'.")
    sys.exit()

try:
    from Levenshtein import ratio
except ImportError:
    print("You have the wrong version of Levenshtein :/ Try running this in your terminal: 'pip install --upgrade Levenshtein==0.16.0'.")
    sys.exit()


__author__ = "Daniel Adam Nuccio"
__license__ = "GPL 3.0"
__maintainer__ = "Daniel Adam Nuccio"
__email__ = "z1741403@students.niu.edu"
__description__ =("A set of Python utilities to parse Google Scholar data")

def main(author_ids, output_file, random_interval_precaution, article_limit_precaution, verbosity, api_key, levenshtein_threshold):
    '''
    Implement Scholarly's ProxyGenerator to use ScraperAPI.
    Scholarly maintainers have said it should only need to be called once (although Scraper API people recommend multiple times).
    Scholarly v1.4.2 worked, but v1.4.4 lost functionality as maintainers set up feature to redirect premium proxies to free proxies that would work inconsistently.
        Maintainers say issue will be addressed in v1.5.
        Issue fixed in v1.4.5.
        Now proxy set up once, but called before each action requiring the prox.y
    '''

    pg = ProxyGenerator()
    proxy_success = False
    if api_key is not None:
        while proxy_success == False:
            proxy_success = pg.ScraperAPI(str(api_key)) 
        if verbosity == 1 or verbosity == 2: print('\nProxy setup was successful at ' + str(time.asctime(time.localtime(time.time()))))
    else:
        pg = None

    #Retrieve the author's data, fill-in, and return list of dictionaries containing author and pub info
    dicList = []
    for a_id in author_ids:
        if verbosity == 1 or verbosity == 2: print('\nProcessing: ', a_id)

        ##Process valid IDs while flagging invalid IDs
        try:

            ###Search author ID
            if pg is not None: scholarly.use_proxy(pg, pg)
            id = scholarly.search_author_id(a_id)
            name = id['name']
            if verbosity == 1 or verbosity == 2: print(name)

            ###Fill author container with with basic info for author and publications
            ###Also provides number of pubs
            if pg is not None: scholarly.use_proxy(pg, pg)
            author = scholarly.fill(id, sections=['basics', 'publications'] )
            numPub = len(author['publications'])
            if verbosity == 1 or verbosity == 2: print(name + ' has ' + str(numPub) + ' publications\n')

            ###Generate random intervals to be used between scraping pub info if random interval preacution left on
            random_intervals = []
            if random_interval_precaution == 'Yes': random_intervals = genRandList(numPub)
            ###Set limit of 1, 5, or none for number of publications scraped; primarily for testing and troubleshootin purposes
            article_limit = determine_article_limit(article_limit_precaution, numPub)

            ###Create a list of dictionaries containing publication info
            dicList = gather_pub_info(author, random_intervals, dicList, random_interval_precaution, article_limit, verbosity, pg, api_key)

        except AttributeError:
            print('An AttributeError occurred for ' + a_id)
            print('Please check to make sure this ID is correct.')

        except DOSException:
            print(f'A Could not get info for: {a_id}', '\nA DOSException has occurred')

        except MaxTriesExceededException:
            print(f'A Could not get info for: {a_id}', '\nA MaxTriesExceededException has occurred')

        except Exception as exc:
            print(f'Could not get info for: {a_id}, exception: {exc}')

    print()

    #Produce final .tsv file
    produce_final_tsv(output_file, dicList, verbosity, levenshtein_threshold, api_key, random_interval_precaution)
    if verbosity == 1 or verbosity == 2: print('\n' + output_file + ' created at ' + str(time.asctime(time.localtime(time.time()))))

#Create class for FilesNPathsError
class FilesNPathsError(Exception):
    pass

#Check input paths and process author IDs
def processInput(arg_dict):
    user_ids = arg_dict['user_ids']
    verbosity = arg_dict['verbosity']
    file_type = arg_dict['file_type']

    #Check input file and path
    #Is input a file or a single ID?
    if len(user_ids) < 2:
        head, tail = os.path.split(user_ids[0])
        ext = pathlib.Path(tail).suffix
        ext = ext.lower()

        ##Does input path exist?
        if len(head) > 0:
            if not os.path.exists(user_ids[0]):
                try:
                    raise FilesNPathsError()
                except FilesNPathsError as e:
                    print('FilesNPathsError: Your input path does not exist. Please try again.')
                    sys.exit(1)

        ##Does file exist?
        if os.path.isfile(user_ids[0]):

            ###Does user have permission to read?
            if not os.access(user_ids[0], os.R_OK):
                try:
                    raise FilesNPathsError()
                except FilesNPathsError as e:
                    print('FilesNPathsError: You do not have permission to read this file :(')
                    sys.exit(1)

            ###Is file empty?
            if os.stat(user_ids[0]).st_size==0:
                try:
                    raise FilesNPathsError()
                except FilesNPathsError as e:
                    print('FilesNPathsError: Your input file is empty :(')
                    sys.exit(1)

            ###Is file REALLY plain text?
            try:
                open(os.path.abspath(user_ids[0]), 'r').read(512) #Do I need to close this?
            except UnicodeDecodeError:
                try:
                    raise FilesNPathsError()
                except FilesNPathsError as e:
                    print("FilesNPathsError: Your file does not seem to be plain a text file :/")
                    sys.exit(1)

            ###Process file if above conditions are met
            ###If .txt file
            if ext == '.txt' and file_type == 'txt':
                preIdList = canFileBeProcessed(user_ids, verbosity)
                author_ids = processPreIdList(preIdList, verbosity)

            ###If .tsv file
            elif ext == '.tsv' and file_type == 'tsv':
                preIdList = canFileBeProcessed(user_ids, verbosity)
                preIdList = [sub_id for combined_id in preIdList for sub_id in combined_id.split("\t")]
                author_ids = processPreIdList(preIdList, verbosity)

            ###If .csv file
            elif ext =='.csv' and file_type == 'csv':
                preIdList = canFileBeProcessed(user_ids, verbosity)
                preIdList = [sub_id for combined_id in preIdList for sub_id in combined_id.split(",")]
                author_ids = processPreIdList(preIdList, verbosity)

            ###If idk
            elif ext != '.txt' and ext != '.tsv' and ext != '.csv' and file_type == 'idk':
                if verbosity == 1 or verbosity == 2: print('You really should know what kind of file you want to process, but we will do our best :)')
                preIdList = canFileBeProcessed(user_ids, verbosity)
                preIdList = [sub_id for combined_id in preIdList for sub_id in combined_id.split()]
                preIdList = [sub_id for combined_id in preIdList for sub_id in combined_id.split(",")]
                author_ids = processPreIdList(preIdList, verbosity)

            else:
                print('If you would like to process a file other than a .txt file, please use the \'--file-type\' option in the command line, making sure that the file extension matches your selection for \'--file-type\'')
                sys.exit(1)

        ##If --user-ids input has one element and is not a file
        ##Process as single ID
        else:
            if verbosity == 1 or verbosity == 2: print("Input does not appear to be a file. Therefore it will be processed as a single user ID.")
            if verbosity == 1 or verbosity == 2: print('Processing ID:')
            author_ids = [id.replace(',', '') for id in user_ids]
            if verbosity == 1 or verbosity == 2: print(author_ids[0])

    ##If --user-ids input is a list of IDs
    ##Process list of IDs
    else:
        if verbosity == 1 or verbosity == 2: print('You have entered a list of IDs.')
        if verbosity == 1 or verbosity == 2: print('The following ID(s) will be processed:')
        author_ids = [id.replace(',', '') for id in user_ids]
        if verbosity == 1 or verbosity == 2: print(*author_ids, sep='\n')
    return author_ids

#Can the input file be opened
def canFileBeProcessed(user_ids, verbosity):
    if verbosity == 1 or verbosity == 2: print('Processing ' + str(user_ids[0]))

    #Try opening files
    #Process file into preIdList
    try:
        with open(user_ids[0], 'r') as in_f:
            preIdList = [id.strip() for id in in_f]
    except:
        print('Your file could not be processed :( Please make sure it is in fact a properly formatted text file.')
        sys.exit(1)

    return preIdList

#Process preIdList
#Create final list of author_ids
def processPreIdList(preIdList, verbosity):

    #Remove commas
    author_ids = [id.replace(',', '') for id in preIdList]

    #Remove lines with multiple strings
    if verbosity == 1 or verbosity == 2:
        author_ids = list(filter(None, [id if len(id.split()) == 1 else print('The following ID was removed ' + str(id)) for id in author_ids]))
    else:
        author_ids = list(filter(None, [id  for id in author_ids if len(id.split()) == 1]))

    if verbosity == 1 or verbosity == 2:
        print('\nThe following author ids will be processed:')
        print(*author_ids, sep='\n')

    return author_ids

#Check output file and path
def checkOutputFile(arg_dict):
    verbosity = arg_dict['verbosity']
    replace_file = arg_dict['replace_file']
    output_file = arg_dict['output_file']
    head, tail = os.path.split(output_file)
    if len(head) > 0:

        #Does path exist?
        if not os.path.exists(head):
            try:
                raise FilesNPathsError()
            except FilesNPathsError as e:
                print('FilesNPathsError: Your output path is invalid. Please try again.')
                sys.exit(1)

        #Does user have permissions to write to directory?
        if not os.access(output_file, os.W_OK):
            try:
                raise FilesNPathsError()
            except FilesNPathsError as e:
                print('FilesNPathsError: You do not have permission to write to this directory :(')
                sys.exit(1)

    #Does File Already Exist?
    if os.path.isfile(output_file):
        if replace_file == 'Yes':
            if verbosity == 1 or verbosity == 2: print('Proceeding to overwrite existing file: ' + output_file)
        else:
            try:
                raise FilesNPathsError()
            except:
                print("FilesNPathsError: Let's try not to overwrite existing files")
                sys.exit(1)

    return output_file

#Allow user to set article limit (technically of 1 or 5) for testing and troubleshooting purposes (helps to avoid upsetting Goliath)
def determine_article_limit(article_limit_precaution, number_of_publications):

    limit = 0

    if article_limit_precaution == None:
        limit = number_of_publications
    elif number_of_publications <= article_limit_precaution:
        limit = number_of_publications
    else:
        limit = article_limit_precaution

    return limit

#Generate random intervals for time between accessing publications as means to avoid upsetting Goliath
def genRandList(number_of_publications):

    randList = []
    n = 0

    while n < number_of_publications:
        n = n + 1
        ran = randint(30, 150)
        randList.append(ran)

    return randList

#Gather publication info
def gather_pub_info(author, random_intervals, dicList, random_interval_precaution, article_limit, verbosity, pg, api_key):

    #Iterate through publications in author dictionary
    i = 0
    for publication in author['publications']:
        if i < article_limit:

            try:
                ##Fill publication info and append dictionary to list
                if pg is not None: scholarly.use_proxy(pg, pg)
                nPub = scholarly.fill(author['publications'][i])

                dicList.append(nPub)
                if verbosity == 1 or verbosity == 2: print("Gathered data for pub " + str(i+1) + " at ", time.asctime(time.localtime(time.time())))
                if verbosity == 2: print(nPub, '\n')


            except DOSException:
                print(f'A Could not get info for: {a_id}', '\nA DOSException has occurred')

            except MaxTriesExceededException:
                print(f'A Could not get info for: {a_id}', '\nA MaxTriesExceededException has occurred')

            except Exception as exc:
                print(f'Could not get info for: {publication}, exception: {exc}')
                if verbosity == 1 or verbosity == 2: print("Could NOT gather data for pub " + str(i+1))

            ##Night night for program for randomly determined interval in random_intervals list
            if random_interval_precaution == 'Yes':
                t = random_intervals[i]
                if verbosity == 1 or verbosity == 2: print("Sleep for " + str(t) + " seconds at " + str(time.asctime(time.localtime(time.time()))))
                time.sleep(t)

            i = i + 1

    return dicList

#Write publication info to a .tsv file
def produce_final_tsv(output_file, dicList, verbosity, levenshtein_threshold, api_key, random_interval_precaution):
    with open(output_file, 'wt') as o_file:
        tsv_writer = csv.writer(o_file, delimiter='\t')
        if verbosity < 2: tsv_writer.writerow(['Title', 'Authors', 'Year', 'Journal', 'Volume', 'Number', 'Pages', 'Citations', 'DOI'])
        if verbosity ==2: tsv_writer.writerow(['Title', 'Authors', 'Year', 'Journal', 'Volume', 'Number', 'Pages', 'Citations', 'DOI', 'DOI Request Status Code', 'levenshtein Ratio'])

        for v in dicList:
            title = v['bib']['title'] if 'title' in v['bib'] else ''
            auth = format_authors(v['bib']['author']) if 'author' in v['bib'] else ''
            year = v['bib']['pub_year'] if 'pub_year' in v['bib'] else ''
            jour = v['bib']['journal'] if 'journal' in v['bib'] else ''
            volu = v['bib']['volume'] if 'volume' in v['bib'] else ''
            numb = v['bib']['number'] if 'number' in v['bib'] else ''
            page = v['bib']['pages'] if 'pages' in v['bib'] else ''
            cite = v['num_citations'] if 'num_citations' in v else ''

            # get an ASCII-only version of the title to avoid downstream API snafu:
            ascii_title = ''.join([i if ord(i) < 128 else '' for i in title])

            #Get make doi request
            status, doiReq = getDOI(ascii_title, api_key, verbosity, random_interval_precaution)

            levenshteinRatio, doi = processDOI(ascii_title, doiReq, levenshtein_threshold, verbosity, status)

            if verbosity == 2: print(f'Title: "{title}"; Doi: {doi}\n')

            if verbosity < 2: tsv_writer.writerow([title, auth, year, jour, volu, numb, page, cite, doi])
            if verbosity ==2: tsv_writer.writerow([title, auth, year, jour, volu, numb, page, cite, doi, status, levenshteinRatio])

#Reformat authors from scholarly format to desired format
def format_authors(authors_in_scholarly_format):
    author_list = authors_in_scholarly_format.split(' and ')
    name_breakdown = []
    new_author_string = ''
    last_name = ''
    first_and_mi = []
    initials = []

    for name in author_list:
        name_breakdown = name.split(' ')
        last_name = name_breakdown[-1]
        first_and_mi = name_breakdown[:-1]
        new_author_string = new_author_string + last_name + ', ' + ' '.join(first_and_mi) + "; "

    return new_author_string

def getDOI(ascii_title, api_key, verbosity, random_interval_precaution):
    '''
    Function that creates url Cross Ref API base and urllib-processed title
        and then attempts to retrieve doi info via Requests package and Cross Ref API

    Also used optional Scraper API if if API key is given.
    '''

    try:

        #Create url for doi retrieval through API Cross Ref
        base = 'https://api.crossref.org/works?rows=5&query.title='
        url = base + urllib.parse.quote_plus(ascii_title)

        #Setup Scraper API key for doi retrieval if one is given
        #Then use make a request through API Cross Ref with or without Scraper API depending on the above
        if api_key is not None:
            payload = {'api_key': api_key, 'url': str(url)}
            r = requests.get('http://api.scraperapi.com', params=payload)
        else:
            r = requests.get(url)

            ##Allow for use of ranom interval feature for DOIs if selected
            if random_interval_precaution == 'Yes':
                t = randint(30, 150)
                if verbosity == 1 or verbosity == 2: print("\nSleep for " + str(t) + " seconds at " + str(time.asctime(time.localtime(time.time()))))
                time.sleep(t)

        #Get request status code
        request_status_code = r.status_code

        #Return request status code and info if request successful
        #Use backup doi retrieval system if request is unsuccessful
        if request_status_code == 200:
            doiReq = r.text
            return request_status_code, doiReq
        else:
            print('Attempting DOI retrieval via backup')
            backupStatus, doiReq = backupDOIRetrieval(ascii_title, verbosity)
            return backupStatus, doiReq

    except Exception as e:
        print(f'\n - Failed to get DOI for the pub "{title}" as someone was not happy: "{e}".')

        return 0, ''

def backupDOIRetrieval (ascii_title, verbosity):
    '''
    Backup doi retrival function:
    Attempts doi retrival with method from Habanero.
    This method cannot be used with Scraper API.
    If unsuccessful, the code is put to sleep for 10s as Cross Ref API may be becoming overwhelmed
    '''

    try:
        cr = Crossref()
        results = cr.works(query = ascii_title, limit = 1)
        backupStatus = results['status']

        return backupStatus, results

    except Exception as e:
        print(f'\n - Backup failed to get DOI for the pub "{title}" as someone was not happy: "{e}".')
        print('\nTaking a 10s nap')
        time.sleep(10)
        return 0, ''

def processDOI(ascii_title, doiReq, levenshtein_threshold, verbosity, status):
    '''
    Function to process retrieved DOI info:
    If the primary or backup attempt was successful, the retrieved DOI and associated title are retrieved
        and a Levenshtein ratio is obtained by comparing the the original title and doi-associated title.
        If the Levenshtein ratio is greater than or equal to the preset or manually-set threshold, the Levenshtein ratio and doi are returned.
        If the Levenshtein ratio is less than the preset or manually-set threshold, only the Levenshtein ratio is returned.

    If both the primary and backup attempts were unsuccessful, a failure message is printed and the word "Failure" returned in place of a a Levenshtein ratio.
    '''

    #Process returned data if primary retrieval attempt was successful
    if status == 200:

        try:

            if verbosity == 1 or verbosity == 2: print('Processing doi for: ' + str(ascii_title) + ' at ' + str(time.asctime(time.localtime(time.time()))) )
            data = json.loads(doiReq)
            items = data['message']['items']

            ##Retrieve doi and title associated with doi
            for item in items:
                if 'title' not in item:
                    continue
                else:
                    preDOI = [z['DOI'] for z in data['message']['items'] ]
                    doiTitle = [z['title'] for z in data['message']['items'] ]

            ##Obtain Levenshtein ratio
            levenshteinRatio = ratio(ascii_title.lower(), doiTitle[0][0].lower())

            ##Determine if Levenshtein ratio meets threshold
            if levenshteinRatio >= levenshtein_threshold:
                return levenshteinRatio, preDOI[0]
            else:
                return levenshteinRatio, ''


        except Exception as e:
            print(f'\n - Failed to get DOI for the pub "{ascii_title}" due to issue with Cross Ref data: "{e}".')
            return 0, ''

    #Process returned data if backup retrieval attempt was successful
    elif status == 'ok':

        try:

            ##Retrieve doi and title associated with doi
            if verbosity == 1 or verbosity == 2: print('Retrieving doi for: ' + str(ascii_title) + ' at ' + str(time.asctime(time.localtime(time.time()))) )
            preDOI = [z['DOI'] for z in doiReq['message']['items'] ]
            doiTitle = [z['title'] for z in doiReq['message']['items'] ]

            ##Obtain Levenshtein ratio
            levenshteinRatio = ratio(ascii_title.lower(), doiTitle[0][0].lower())

            ##Determine if Levenshtein ratio meets threshold
            if levenshteinRatio >= levenshtein_threshold:
                return levenshteinRatio, preDOI[0]
            else:
                return levenshteinRatio, ''

        except Exception as e:

            print(f'\n - Backup failed to get DOI for the pub "{title}" as someone was not happy: "{e}".')
            return 'Failure', ''


    else:
        print(f'\n - Backup failed to get DOI for the pub "{title}" as someone was not happy: "{e}".')
        return 'Failure', ''


if __name__ == "__main__":
    #Use Argparse to Take In Commandline Arguments
    parser = argparse.ArgumentParser(description = __description__, allow_abbrev= False) #provide description
                                                                                         #disable abbreviated args

    ##Required arguments ('user-ids' and 'output-file')
    requiredNamed = parser.add_argument_group('Required Arguments')
    requiredNamed.add_argument('--user-ids', nargs = "+",
                                required=True,
                                help = "One or more IDs entered via the commandline or in a single .txt file with the appropriate '.txt' extension")
    requiredNamed.add_argument("--output-file",
                                required = True,
                                help = "Output file with publication info in .tsv format")

    ##Precautionary arguments (e.g. 'api-key', 'random-interval-precaution', and 'article-limit-precaution')
    precautionsNamed = parser.add_argument_group('Precautions to Avoid Angering Google a.k.a Goliath')
    precautionsNamed.add_argument("--api-key", default = None,
                                    help = "Key for Scraper API. Will allow for implementation of rotating proxies.")
    precautionsNamed.add_argument("--random-interval-precaution", choices = ['Yes', 'No'], default = 'No',
                                    help = "Scrapes article data at random intervals of 30-150s to appear more human and decrease the liklihood of making Google angry.(This feature will be turned on by default. Disable at your own risk...)")
    precautionsNamed.add_argument("--article-limit-precaution", choices = [None, 1, 5], type = int, default = None,
                                    help = "Limit the number of articles scraped from Google to 1 or 5 for testing purposes.")

    ##Miscellaneous arguments
    miscellaneousNamed = parser.add_argument_group('Arguments to customize your experience with this program.')
    miscellaneousNamed.add_argument('--verbosity', choices = [0, 1, 2], type = int, default = 1,
                                        help = 'Customize how much information you want concerning the progress of your search. (Default equals 1. Error messages will always be printed because there is always room for self-improvement ;)')
    miscellaneousNamed.add_argument('--replace-file', choices = ['Yes','No'], default = 'No',
                                        help = 'Force program to overwrite existing output files.')
    miscellaneousNamed.add_argument('--file-type', choices = ['txt', 'tsv', 'csv', 'idk'], default = 'txt',
                                        help = 'The preferred file type is .txt, but if you really want to try another basic text format you can.')
    miscellaneousNamed.add_argument('--levenshtein-threshold', default = 0.95, type=float,
                                        help = 'Similarity threshold between 0.0-1.0 for Title and DOI reverse lookup title')

    #Check if proper arguments are given
    known_args, unknown_args = parser.parse_known_args()

    if unknown_args != []:
        print("It appears you have entered an invalid argument :/")
        [print(unknown) for unknown in unknown_args if unknown.startswith('--')]
        sys.exit(1)

    arg_dict = known_args.__dict__

    if arg_dict['verbosity'] == 1 or arg_dict['verbosity'] == 2: print('\nProgram started at ' + str(time.asctime(time.localtime(time.time()))))

    if arg_dict['verbosity'] == 1 or arg_dict['verbosity'] == 2:
        print('\nYou entered the following arguments:')
        for k, v in arg_dict.items(): print(k, ': ', v)
        print('\n')

    #Required to disable useless warning (recommended by Scholarly maintainers)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    #Process --user-ids input
    user_ids = processInput(arg_dict)

    #Process --output-file input
    output_file = checkOutputFile(arg_dict)

    #Main
    main(user_ids, output_file, arg_dict['random_interval_precaution'], arg_dict['article_limit_precaution'], arg_dict['verbosity'], arg_dict['api_key'], arg_dict['levenshtein_threshold'])