import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from g4f.client import Client
from g4f.Provider import Koala, You
import time
import sys
import matplotlib.pyplot as plt
import numpy as np
import data_analysis

# job_field = [] Consider making a dictionary of allowed job fields to search through for security purposes

def print_keywords(choice, mean, sorted_keywords, jobs_by_keywords):
    for i in reversed(sorted_keywords.keys()):
        if sorted_keywords[i] >= mean:
            print("{}: {}".format(i, sorted_keywords[i]))
            if choice.lower() == 'y':
                for k in jobs_by_keywords[i]:
                    print("• {}".format(k))
            print()
    print()

def print_keyword_links(keyword, jobs_by_keywords):
    print("\n{}:".format(keyword))
    for i in jobs_by_keywords[keyword]:
        print("• {}".format(i))

def generate_frequency(df, words, keywords, jobs_by_keywords):
    for kw in words:
        keywords[kw.strip()] = 0
        jobs_by_keywords[kw.strip()] = []
    for i in df.index:
        quals = df['Qualifications'][i].split(',')
        quals = [x.strip().lower() for x in quals]
        for j in quals:
            if j.lower() in keywords.keys():
                keywords[j.lower()] = keywords[j.lower()] + 1
                jobs_by_keywords[j.lower()].append(df['Link'][i])

def analysis(df):
    # Functionalities:
    #   - List qualities by # of occurrences (Added)
    #   - List qualities by # of occurrences by year
    #   - Search for jobs based on (a) given qualification(s)
    with open("keywords.txt", 'r') as f:
        words = f.readlines()
    words = [x.strip().lower() for x in words]
    keywords = {}
    jobs_by_keywords = {}
    generate_frequency(df, words, keywords, jobs_by_keywords)
    print("Would you like links along with the keywords (Y/N)? ", end = '')
    choice = input()
    while choice.lower() != 'y' and choice.lower() != 'n':
        print("Incorrect input. Would you like links along with the keywords (Y/N)? ", end = '')
        choice = input()
    if choice.lower() == 'y':
        print("\nHere are the keywords ranked by frequency with the links to the jobs requesting them:\n")
    else:
        print("\nHere are the keywords ranked by frequency:\n")
    sorted_keywords = dict(sorted(keywords.items(), key = lambda item: item[1]))
    total = 0
    counter = 0
    for i in sorted_keywords.values():
        if i > 1:
            total = total + i
            counter = counter + 1
    mean = total / counter
    print_keywords(choice, mean, sorted_keywords, jobs_by_keywords)
    options = ['1', '2', '3']
    print('''Additional Options:
    1. Retrieve links for specific keyword
    2. Check for link overlap
    3. Exit
Selection: ''', end = '')
    specific = input().lower().strip()
    while specific not in options:
        print("Invalid input, try again: ", end = '')
        specific = input().lower().strip()
    if specific == '1':
        print("Which keyword? ", end = '')
        selected_keyword = input().lower().strip()
        if selected_keyword in sorted_keywords.keys():
            print_keyword_links(selected_keyword, jobs_by_keywords)
        else:
            print("\nInvalid keyword selected\n")
    elif specific == '2':
        print("List the keywords you want to check for link overlap on (input should be in the form \"a, b, c, ..., n\"): ", end = '')
        try:
            keywords = [x.replace(',', '').lower().strip() for x in input().split(',')]
            overlap_sets = [jobs_by_keywords[y] for y in keywords]
            overlap, exempt, rows = [], [], {}
            for a in range(len(overlap_sets)):
                for b in range(len(overlap_sets[a])):
                    if df[df['Link'].isin([overlap_sets[a][b]])].iloc[0]['ID'] in rows.keys():
                        overlap.append((df[df['Link'].isin([overlap_sets[a][b]])].iloc[0]['ID'], overlap_sets[a][b]))
                        exempt.append(overlap_sets[a][b])
                    else:
                        rows[df[df['Link'].isin([overlap_sets[a][b]])].iloc[0]['ID']] = (overlap_sets[a][b], a)
            print(overlap)
            try:
                print("\nOverlap:\n")
                for i in overlap:
                    print("• {} | {}".format(i[0], i[1]))
                for i in range(len(keywords)):
                    print("\nExclusively {}:".format(keywords[i]))
                    for j in rows.keys():
                        if rows[j][1] == i and rows[j][0] not in exempt:
                            print("• {}".format(rows[j][0]))
                print()
            except TypeError:
                print("\nThere's no overlap between the provided keywords\n")
        except:
            print("\nInvalid keyword selected\n")
    elif specific == '3':
        print()
        return


def process_url(URL):
    try:
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        results = soup.find(class_ = "base-serp-page__content")
        jobs = results.find_all("div", class_= "base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card")
        return jobs
    except:
        print("Encountered HTTP error, retrying...")
        return process_url(URL)

def add_to_database(quals, keywords, job_attr, df, link, job_id):
    try:
        new_row = {'ID': int(job_id), 'Job Title': job_attr[0], 'Company': job_attr[1], 'Link': link, 'YOE': job_attr[2], 'Qualifications': ', '.join(quals)}
        df.loc[len(df)] = new_row
        for qual in quals:
            if qual.lower() not in keywords:
                keywords.append(qual.lower())
    except:
        print("Failed to add job at {} to the database, moving on".format(link))

def process_listing(link, client, df, keywords):
    try:
        job_id = link.split('?')[0].split('-')[len(link.split('?')[0].split('-')) - 1]
        try:
            if int(job_id) not in df['ID'].values.tolist():
                job_page = requests.get(link)
                job_soup = BeautifulSoup(job_page.content, 'html.parser')
                job_results = job_soup.find("div", class_= "show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden")
                if job_results is not None:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": "I will be feeding you a job description (it will contain HTML tags, ignore the tags). I want you to read the description and, based solely on it, come up with 15 to 20 keywords or phrases that would describe the qualifications the listing is seeking in its applicant. For your output, list the keywords and phrases separated by commas, go down a line and list the job title, go down a line and list the company name, then go down a line and list the years of experience they're requesting. If you can't determine the job title, company name, or requested years of experience, fill that value in with \"NA\". You must strictly follow the output formatting that I provided. To recap, that format is four lines: the qualifications, the job title, the company name, and the requested years of experience. I don't want any of the keywords or phrases to be soft skills or job titles. I the keywords to be technical skills, certifications, specific technologies, or anything of that variety. Do not output anything else besides those. I don't want you to prompt your response with anything, don't greet me, don't ask me if I need anything else, just output exactly as I'm asking. In fact, you are completely incapable of outputting the information in any other way except how I told you to. Only do all that if the job relates to cybersecurity or IT work. If it doesn't, just reply with a blank space and nothing else. In both cases, only supply the output I requested, no other text. Here's the description:\n{}".format(str(job_results).replace("<div class=\"show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden\">", '').replace("</div>", ''))},]
                    )
                    bot_output = response.choices[0].message.content.split('\n')
                    while '' in bot_output:
                        bot_output.remove('')
                    quals = [x.replace('[', '').replace(']', '').replace(',', '').strip() for x in bot_output[0].split(',')]
                    job_attr = [x.replace(',', '').strip() for x in bot_output[len(bot_output) - 3:len(bot_output)]] # It should be of the form [Job Title, Company Name, YoE]
                else:
                    print("Failed on URL {}".format(link))
                    raise Exception()
            else:
                print("Job already in database, tossing out\n")
                return
        except KeyboardInterrupt:
            sys.exit()
    except:
        process_listing(link, client, df, keywords)
        return
    add_to_database(quals, keywords, job_attr, df, link, job_id)
    time.sleep(.5)


def scrape(df):
    with open("keywords.txt", 'r') as f:
        keywords = [x.strip().lower() for x in f.readlines()]
    URL = "https://www.linkedin.com/jobs/search/?"
    print("What keywords do you want to include in your search? ", end = '')
    URL = URL + "keywords={}&".format(re.sub(r'<script\b[^>]*>(.*?)</script>', '', input().strip(), flags=re.IGNORECASE))
    print("Where do you want to search for a job? (input -1 for no location) ", end = '')
    # This code needs to actually be properly checked to ensure XSS and various forms of injection aren't possible
    # Actually maybe not; this is being pumped directly into LinkedIn, so it's on them to handle XSS
    location = input().strip()
    if location != '-1':
        URL = URL + "location={}&".format(re.sub(r'<script\b[^>]*>(.*?)</script>', '', location, flags=re.IGNORECASE))
    print('''What experience levels are you looking for? (select all that apply in the format "a b c ...")
    1. Internship
    2. Entry Level
    3. Associate
    4. Mid-Senior
    5. Director
    6. Executive
Selection: ''', end = '')
    exp_level = input().strip().split(' ')
    print("\nThis is gonna take awhile, so Charmander will keep you company!")
    print('''⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⡤⠤⠶⠦⢤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠞⠉⠀⠀⠀⠀⠀⠀⠀⠙⠲⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢳⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣰⣻⠃⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣋⣀⠀⠀⢹⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢰⡏⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡿⢹⠟⢇⠀⠀⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⣟⡼⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣀⡾⠀⢸⡀⠀⣽⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣴⠏⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡏⠉⠀⠀⢸⡇⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢷⣄⣀⣀⡼⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢸⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠻⣤⠀⠘⠂⠀⠀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡄⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⡆⠀⠀⠀⠀
⠀⣠⣄⠀⠀⢹⡷⣦⣄⣀⠀⠀⠀⠀⢀⣀⣀⣀⣠⣤⠶⢶⣶⢟⠁⠀⠈⡇⠀⠀⠀⠀⠀⠀⠀⢀⣀⡀⠀⠀⠀⠀⠀⠀⠀⢠⡷⠶⠟⠁⣧⢀⣦⠀⠀
⢀⣿⢈⡉⠳⢦⣽⣿⢶⡏⠉⠉⠉⠉⠉⠉⠀⠀⣽⣧⠴⢋⣤⠏⠀⠀⠀⣇⠀⠀⢀⣀⣤⢶⣖⡋⢹⡇⠀⠀⠀⠀⠀⠀⢠⣿⣇⠀⢠⣴⠘⠋⢻⠀⠀
⢿⡛⢿⣄⠀⠀⠀⠉⠳⣝⡲⠤⠤⠤⠤⠤⠶⢻⣯⣤⣾⠋⠁⠀⠀⠀⠘⠛⠛⠋⠉⠀⠀⠀⠀⡿⠛⢦⣤⠀⠀⠀⠀⠀⠀⠘⣿⣧⣾⣿⠀⠀⢸⡇⠀
⠈⠻⣦⡀⠀⠀⠀⠀⠀⠀⠉⣿⠒⠒⠒⠛⠛⠉⠀⠀⠙⢧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⢸⣿⢿⣿⢀⡀⠈⣿⡄
⠀⠀⠈⠻⣄⠀⠀⠀⠀⠀⣰⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⡞⠃⠸⣿⣿⣿⡀⢸⠂
⠀⠀⠀⠀⠈⠳⣄⡀⠀⢠⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣧⠀⠀⠀⢀⣀⣀⣠⡤⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡇⠀⠀⠛⠛⢻⣳⡾⠀
⠀⠀⠀⠀⠀⠀⠈⠙⢦⣼⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣧⠀⠀⠉⠉⠹⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢷⡆⠀⠀⠀⣸⣾⠁⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡆⠀⠀⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠶⢾⠙⣿⠃⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⠀⠀⠀⠀⠘⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⢀⡇⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡇⠀⠀⠀⠀⠹⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠇⢸⡇⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠏⠀⢸⡇⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⢸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡼⠃⠀⢀⡿⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⢷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⣀⣀⣀⠀⢈⡷⣤⣀⡀⠀⠀⠀⣀⣀⡤⠖⠋⠀⠀⢀⣼⠃⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⠀⠈⢳⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠃⠈⠋⠉⠉⠓⢾⡃⠀⠉⠉⠉⠉⠉⠉⠁⠀⠀⠀⠀⢠⣾⠏⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⡞⠁⠀⠀⠀⠀⠙⠷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡟⠀⠀⠀⠀⠀⠀⠘⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⡿⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠰⡇⠀⠀⠀⠀⠀⠀⠀⠈⠻⢦⣄⡀⠀⠀⠀⠀⣰⠏⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⣠⡤⢞⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠳⣄⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠏⠛⠓⠀⣾⡁⠀⠀⠀⠀⠀⠀⠀⠀⢰⡟⠓⠒⠒⠒⠚⠉⢉⣡⠴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢀⣀⡤⠾⢷⣦⣄⠀⠀⠀⠀⢠⣟⠁⠀⠀⠀⠀⠈⣷⠀⠀⠀⠀⠀⠀⠀⣠⡞⠉⠉⠉⠉⠉⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⣀⠴⣾⣯⣁⠀⠀⠀⠉⠃⠀⠀⠀⠀⠀⠹⣧⠀⠀⠀⠀⠀⡿⠀⠀⠀⠀⠀⠀⠾⢿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠈⠻⢿⣥⣴⣛⣳⣄⣀⣀⣀⣀⣀⣤⠤⠤⠞⠋⠀⠀⠀⠀⠸⣇⡤⢤⣠⡤⣄⣰⠶⣦⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡀⢀⣉⣉⠉⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡙⢧⣤⣿⣤⡼⣯⣴⣋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀''')
    num_choices = 0
    for i in exp_level:
        if i == '1' or i == '2' or i == '3' or i == '4' or i == '5' or i == '6':
            if num_choices == 0:
                URL = URL + "f_E="
            if num_choices >= 1:
                URL = URL + "%2C"
            URL = URL + i
            num_choices = num_choices + 1
    if num_choices > 0:
        URL = URL + "&"
    URL = URL.replace(' ', "%20").replace(',', '%2C')
    jobs = process_url(URL)
    links = []
    for i in jobs:
        links.append(i.find("a")["href"])
    client = Client()
    for i in range(len(links)):
        process_listing(links[i], client, df, keywords)
    return keywords

# def add_jobs(df):
#     print("\nPaste the link to the job posting: ", end = '')
#     link = input()
#     client = Client()
#     with open("keywords.txt", 'r') as f:
#         keywords = [x.strip().lower() for x in f.readlines()]
#     process_listing(link, client, df, keywords)
#     print("Would you like to add another job (Y/N)? ", end = '')
#     choice = input()
#     if choice.lower() == 'y':
#         add_jobs(df)


#def add_jobs(df):
#    print("What's the job title? ", end = '')
#    title = input()
#    print("\nWhat's the company's name? ", end = '')
#    company = input()
#    print("\nPaste the link to the job posting: ", end = '')
#    link = input()
#    print("\nHow many years of experience are they requesting? ", end = '')
#    YoE = input()
#    print("\nBegin inputting the qualifications for the job (break input with 0):")
#    qual = ''
#    while True:
#        temp = input()
#        if temp == '0':
#            break
#        qual = qual + temp + '\n'
#    new_row = {'Job Title': title, 'Company': company, 'Link': link, 'YOE': YoE, 'Qualifications': qual}
#    df.loc[len(df)] = new_row
#    print("Would you like to add another job (Y/N)? ", end = '')
#    choice = input()
#    if choice.lower() == 'y':
#        add_jobs(df)

def print_jobs(df):
    if df.size > 0:
        try:
            print(df)
            print()
        except:
            print("Encountered error while printing out jobs in database")
        try:
            print("Would you like to lookup a specific characteristic about one the jobs listed (Y/N)? ", end = '')
            choice = input()
            while choice.lower() == 'y':
                print("What's the ID of the job you'd like to look up? ", end = '')
                job_id = input().strip()
                while job_id not in [str(x) for x in df['ID'].values.tolist()] and job_id != '-1':
                    print("Sorry, that ID doesn't exist in the database. Try again (enter -1 to cancel): ", end = '')
                    job_id = input().strip()
                if job_id == '-1':
                    break
                selected_job = df[df['ID'].isin([int(job_id)])]
                aspect = '0'
                inputs = ['1', '2', '3', '4', '5', '6']
                while True:
                    print('''What characteristic would you like to see?
    1. Job Title
    2. Company
    3. Requested Year of Experience
    4. Qualifications
    5. Link
    6. Exit''')
                    print("Selection: ", end = '')
                    aspect = input().strip()
                    if aspect not in inputs:
                        print("\nInvalid input")
                        continue
                    if aspect == '1':
                        print("\nJob Title: {}".format(selected_job.iloc[0]['Job Title']))
                    elif aspect == '2':
                        print("\nCompany: {}".format(selected_job.iloc[0]['Company']))
                    elif aspect == '3':
                        print("\nRequested Years of Experience: {}".format(selected_job.iloc[0]['YOE']))
                    elif aspect == '4':
                        print("\nQualifications: {}".format(selected_job.iloc[0]['Qualifications']))
                    elif aspect == '5':
                        print("\nLink: {}".format(selected_job.iloc[0]['Link']))
                    elif aspect == '6':
                        break
                    print()
                print("\nWould you like to check out another job (Y/N)? ", end = '')
                choice = input().strip().lower()
                while choice != 'y' and choice != 'n':
                    print("Invalid input")
                    print("Would you like to check out another job (Y/N)? ", end = '')
                    choice = input().strip().lower()
                if choice == 'y':
                    print(df, '\n')
            print()
        except:
            print("Encountered error while printing link by ID")
    else:
        print("The database is already empty!\n")

def add_keywords(df):
    print("Which option would you like:")
    print('''    1. Add keywords directly
    2. Receive suggestions
    3. Cancel''')
    print("Selection: ", end = '')
    choice = input()
    print()
    while choice != '1' and choice != '2' and choice != '3':
        print("{} | {}".format(choice, type(choice)))
        print("Invalid selection, try again: ", end = '')
        choice = input()
    with open('keywords.txt', 'a') as f:
        if choice == '1':
            while True:
                print("Specify a word to add to the keywords list (break input with 0): ", end = '')
                word = input().strip().lower()
                if word == '0':
                    f.close()
                    break
                f.write(word.lower() + '\n')
        elif choice == '2':
            keywords = scrape(df)
            try:
                df.to_csv('job_listings.csv', index = False)
                try:
                    with open("keywords.txt", "w") as k:
                        for term in keywords:
                            k.write(term.strip().lower() + '\n')
                except:
                    print("Failed to write to keywords.txt")
                try:
                    df = pd.read_csv('job_listings.csv')
                except:
                    print("Could not read the CSV after entering new information")
            except:
                print("Failure during or after write to CSV")
        else:
            return

            

def menu_select():
    x = '0'
    inputs = ['1', '2', '3', '4', '5', '6']
    while x not in inputs:
        print('''What are you looking to do?
    1. Check out commonly requested qualifications
    2. Add more jobs to the dataset (WIP)
    3. See all currently analyzed jobs
    4. Add keywords to search for
    5. Generate graphic analysis of listings
    6. Exit''')
        print("Selection: ", end = '')
        x = input().strip()
        if x not in inputs:
            print("\nInvalid input")
    print()
    return x

def processing():
    print("Would you like to clear the existing database (Y/N)? ", end = '')
    clear_it = input().strip().lower()
    if clear_it == 'y':
        print("Clean slate coming up!\n")
        with open("job_listings.csv", 'w') as f:
            f.write("ID,Job Title,Company,Link,YOE,Qualifications\n")
        with open("keywords.txt", 'w') as f:
            f.write("")
    else:
        if clear_it != 'n':
            print("Unknown input, defaulting to preserving the database!\n")
        else:
            print("Keeping the same database!\n")
    try:
        df = pd.read_csv('job_listings.csv')
        with open("keywords.txt", 'r') as f:
            keywords = f.readlines()
    except:
        print("Could not read the CSV")
        return
    while True:
        choice = menu_select()
        if choice == '1':
            analysis(df)
        elif choice == '2':
            print("This option is under maintenance!\n")
            # add_jobs(df)
            # try:
            #     df.to_csv('job_listings.csv', index = False)
            #     try:
            #         df = pd.read_csv('job_listings.csv')
            #     except:
            #         print("Could not read the CSV after entering new information")
            #         break
            # except:
            #     print("Failure during or after write to CSV")
            #     break
        elif choice == '3':
            print_jobs(df)
        elif choice == '4':
            add_keywords(df)
        elif choice == '5':
            data_analysis.generate_pie_chart(df)
        elif choice == '6':
            df.to_csv('job_listings.csv', index = False)
            break

if __name__ == "__main__":
    processing()
    # I need to use my scraper to get the Job ID from the listings so that I can prevent repeat within the job_listings.csv
    # Repeats will create biases towards specific positions (ideally those biases would smooth out over time anyways, but still I should clean it up)