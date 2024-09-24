import pandas as pd
import re
import hrequests
from bs4 import BeautifulSoup
import time
import sys
import matplotlib.pyplot as plt
import numpy as np
import json
import psycopg2
from simple_term_menu import TerminalMenu
import os
import urllib.parse
from dotenv import load_dotenv
from g4f.client import Client as OpenAI
from g4f.Provider import You, OpenaiChat
import requests
import warnings

load_dotenv()
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
headers = {"User-Agent": "Mozilla/5.0 (<system-information>) <platform> (<platform-details>) <extensions>"}

connection = psycopg2.connect(host='localhost', database='jobhunter', user=USERNAME, password=PASSWORD)
cursor = connection.cursor()

#client = OpenAI(
#    api_key = "",
#    base_url = "http://172.17.0.1:1337/v1"
#)

client = OpenAI()

#gpt_url = "http://localhost:1337/v1/chat/completions"
#gpt_body = {
#    "model": "gpt-4",
#    "stream": False,
#    "messages": [
#        {"role": "user", "content": ""}
#    ]
#}

#client = OpenAI()

ELMER_FUD = """
      ....
    .'   ,:
  .'      \.___..
.'      .-'   _.'
'.\  \/...-''`\\
  :.'   /   \  :
   :    () () /
   (_ .  '--' ':        .':
     / |_'-- .'       .'.'
     \   \  .'_\    .'.'
    .|__  \/_/:   .'.'
   /          :\.',;'
  .' -./      .'{\|))
  '.   ',_,-.',;'--:
  / '../_   \,;'_.'
  :.   ,''-'-'  \\
   \'.'   / \..':
   .'    /.-.   :
   '.   / \  |''\\
     './--:  /   \._
      \.   '.'._.___:
        '...'
"""

MENU_TEXT = """   _____ _     _     _     _               _____ _             _                 _   _                                                                 
  / ____| |   | |   | |   | |             |_   _( )           | |               | | (_)                                                                
 | (___ | |__ | |__ | |__ | |__             | | |/ _ __ ___   | |__  _   _ _ __ | |_ _ _ __   __ _    __ _   ___  __ ___      ____ ___      _____  ___ 
  \___ \| '_ \| '_ \| '_ \| '_ \            | |   | '_ ` _ \  | '_ \| | | | '_ \| __| | '_ \ / _` |  / _` | / __|/ _` \ \ /\ / / _` \ \ /\ / / _ \/ _ \\
  ____) | | | | | | | | | | | | |  _ _ _   _| |_  | | | | | | | | | | |_| | | | | |_| | | | | (_| | | (_| | \__ \ (_| |\ V  V / (_| |\ V  V /  __/  __/
 |_____/|_| |_|_| |_|_| |_|_| |_| (_|_|_) |_____| |_| |_| |_| |_| |_|\__,_|_| |_|\__|_|_| |_|\__, |  \__,_| |___/\__,_| \_/\_/ \__,_| \_/\_/ \___|\___|
                                                                                              __/ |                                                    
                                                                                             |___/                                                     
"""

def analysis():
    pass

def clean_keywords():
    curr_db = [word for word in pd.read_sql('SELECT * FROM hard_skills ORDER BY frequency DESC', connection)["word"]]
    gpt_message = "I'm going to provide you with a list of terms. Currently, the amount is a bit overwhelming. I would like you to try conservatively grouping related terms into categories. You DO NOT have to put every single term into a category, but ones that are hyperspecific or strongly related to other, existing terms should be cleaned up into categories if possible. Additionally, I'd like you to combine terms that are very related and could fall under the same umbrella. For example, AWS EC2 should be combined with AWS because they're both just AWS. With that all said, here are the terms: {}".format(curr_db)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": gpt_message}],
        stream=False,
    )
    response_text = response.choices[0].message.content
    print(response_text)
    holder = input("Press enter to return to the menu ")

def generate_keywords(description):
    #response = requests.post("http://localhost:8080/backend-api/v2/conversation", json={'messages':[{"role": "user", "content": "You are an expert career advisor tasked with determining what a candidate needs in order to best qualify for a job they found on LinkedIn. Today, you've received the following job description in an email: {}.\n Your job is to generate a JSON containing two attributes: a string array named \"hard skills\" and a string array named \"soft skills\". You need to analyze the provided description and generate keywords that you would associate with the given job that the client will be able to use to help guide them in working towards getting the job. Place any hard skills, technical terms, or certifications that you generate into the \"hard skills\" array, and place any characteristics/personality traits you generate into the \"soft skills\" array. Please restrict the information that you draw from to exclusively the provided information. Additionally, you can only provide the requested JSON as output. No additional preamble, greetings, or formalities will be tolerated and will result in the client immediately dropping you. The output should be able to be copy and pasted into a JSON file and work completely fine.".format(description)}]})
    """
    This part is a bit flawed because it's possible for the AI to generate terms that either a) it hallucinates, or b) are very close to ones that already exist in the DB but not quite the same
    The reason this is troubling is it could skew data inferences one way or another and make a certain keyword seem underepresented due to essentially experiencing a split vote

    Possible Solutions:
        - Manual sanitization and maintenance of the keyword table as to combine keywords deemed to be too similar (most work for me, guarantee that I will be able to handle things as I please)
        - Creation of a machine learning model that could use reinforced learning to try and tell when words are similar enough to combine (probably not super feasible?)
        - Use another AI model to compare words/terms and decide when it's worth combining them (least work required from me, highest or second highest chance of not doing what I want)

    ----------------
    According to LinkedIn's 2024 survey (https://www.linkedin.com/business/learning/blog/top-skills-and-courses/most-in-demand-skills) the top 10 soft skills are:

    Communication, Customer Service, Leadership, Project Management, Management, Analytics, Teamwork, Sales, Problem-Solving, and Research

    I think this is a good baseline, but some of these skills also aren't as applicable to security as a field. As a result, I'm going to add on Adaptability, Independence, and Time Management
    as some generalist options to mix things up. Additionally, I'm going to cut sales as a soft skill because it just doesn't make sense to me in the context of *most* cybersecurity roles. There are some roles
    in cyber that require good interpersonal connection and persuasion, but I wouldn't place that under the umbrella of sales.
    """
    curr_db = pd.read_sql('SELECT * FROM hard_skills ORDER BY frequency DESC', connection)
    gpt_message = "You are an expert career advisor tasked with determining what a candidate needs in order to best qualify for a job they found on LinkedIn. Today, you've received the following job description in an email: {}.\n Your job is to generate a JSON containing a string array named \"hard skills\" and 13 integer attributes named Communication, Customer Service, Leadership, Project Management, Management, Analytics, Teamwork, Problem Solving, Research, Adaptability, Independence, and Time Management. You need to analyze the provided description and select keywords that you would associate with the given job that the client will be able to use to help guide them in working towards getting the job. Place any hard skills, technical terms, or certifications that you generate into the \"hard skills\" array. Please try to avoid being too specific with the hard skills you generate. I don't need specific networking protocols (ex. SSH, NTP, DHCP, etc.) or anything that's that particular. Aim for more general ideas. If possible, lift such terms directly from the description and requirements/qualifications. For the integer elements, I would like you to rate the relevance of their listed role (that being the name of the attribute) as it relates to the job based on the description. The rating will be on a scale of 1 to 10 (where 1-3 is low relevance, 4-6 is moderate relevance, 7-8 is high relevance, and 9-10 is critical for the role). Please restrict the information that you draw from to exclusively the provided information (that being the job description for the hard skills and the listed words for the soft skills). Additionally, you can only provide the requested JSON as output. No additional preamble, greetings, or formalities will be tolerated and will result in the client immediately dropping you. The output should be able to be copy and pasted into a JSON file and work completely fine. Please limit your response to under 1000 characters. Additionally, attempt to avoid making your soft skill answers too specific. Try to stick to general characteristics that would typically be sought out by recruiters unless a particular trait is specifically called for in the job description, in which case you can add it in spite of its specificity.".format(description)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": gpt_message}],
        stream=False,
    )

    
    #response_text = str(response.content.decode('utf-8'))
    response_text = response.choices[0].message.content
    while 'https://discord.com/invite/q55gsH8z5F' in response_text:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": gpt_message}],
            stream=False,
        )
        response_text = response.choices[0].message.content
    try:
        response_json = json.loads(re.search("```json(([\n|\r|\s]*(.*))+)```", response_text).group(1))
        return response_json
    except Exception:
        print("Who told you you could change the output format on me??")
        return generate_keywords(description)

def process_glassdoor(company):
    URL = f"https://www.glassdoor.com/searchsuggest/typeahead?numSuggestions=8&source=GD_V2&version=NEW&rf=full&fallback=token&input={company}"
    try:
        company_info = json.loads(hrequests.get(URL, headers=headers).content.decode('utf-8'))
        URL = "https://www.glassdoor.com/Overview/Working-at-{}-EI_IE{}".format(company, company_info[0]["employerId"])
        company_info = hrequests.get(URL, headers=headers).content.decode('utf-8')
        soup = BeautifulSoup(company_info, 'html.parser')
        extracted_rating = soup.find('p', attrs={"class": re.compile("rating-headline-average_rating__[0-9a-zA-Z]{5}")})
        print("Glassdoor processed", end="...")
        #print(extracted_rating == None)
        if extracted_rating != None:
            return (URL, extracted_rating.text.strip())
        else:
            return ("", "NaN")
    except Exception:
        print("Looks like there's no Glassdoor page for {}".format(company), end="...")
        return ("", "NaN")

def process_linkedin(content, requested_job):
    #print(content)
    soup = BeautifulSoup(content, 'html.parser')
    links = [link['href'] for link in soup.find_all('a', attrs={"href": re.compile("https://www\.linkedin\.com/jobs/view/[^\s]+&trk=public_jobs_jserp-result_search-card")})]

    for link in links:
        job_title = None
        salary = None
        company = None
        description = None
        keywords = None
        job_type = None
        location = None
        while True:
            job_posting = hrequests.get(link, headers=headers)
            job_soup = BeautifulSoup(job_posting.content, 'html.parser')

            if job_title == None:
                job_title = job_soup.find('h1', class_ = "top-card-layout__title font-sans text-lg papabear:text-xl font-bold leading-open text-color-text mb-0 topcard__title")

            salary = job_soup.find('div', class_ = "salary compensation__salary")
            if salary == None:
                salary = "NaN"
            else:
                salary = salary.text.strip()
            
            if company == None:
                company = job_soup.find('a', class_ = "topcard__org-name-link topcard__flavor--black-link")
            
            if description == None:
                description = job_soup.find('div', class_ = re.compile("show-more-less-html__markup show-more-less-html__markup--clamp-after-5[\r|\n|\s]*relative overflow-hidden")) # This is the div class that contains the description
            
            if job_type == None:
                job_type = job_soup.find('span', class_ = "description__job-criteria-text description__job-criteria-text--criteria")

            if location == None:
                location = job_soup.find('span', class_ = "topcard__flavor topcard__flavor--bullet")

            if job_title == None or company == None or description == None or description == None or location == None:
                continue

            break

        print("LinkedIn listing retrieved", end="...")
        glassdoor_link, rating = process_glassdoor(company.text.strip())
        keywords = generate_keywords(description.text.strip())
        print("Keywords generated", end="...")
        hard_skills = str([skill.replace('\'', '').replace('\"', '').lower() for skill in keywords["hard skills"]]).replace('[', '{').replace(']', '}').replace('\'', '\"')
        print(hard_skills)
        #print(keywords)

        cursor.execute("INSERT INTO Companies (name, rating, link) SELECT %(name)s, %(rating)s, %(link)s WHERE NOT EXISTS (SELECT name FROM Companies WHERE name = %(name)s);", {'name': company.text.strip(), 'rating': rating, 'link': glassdoor_link})
        cursor.execute("INSERT INTO Jobs (name, salary, link, company, type, hard_skills, location, Communication, Customer_Service, Leadership, Project_Management, Management, Analytics, Teamwork, Problem_Solving, Research, Adaptability, Independence, Time_Management, requested_job) VALUES (%(name)s, %(salary)s, %(link)s, %(company)s, %(type)s, %(hard_skills)s, %(location)s, %(Communication)s, %(Customer_Service)s, %(Leadership)s, %(Project_Management)s, %(Management)s, %(Analytics)s, %(Teamwork)s, %(Problem_Solving)s, %(Research)s, %(Adaptability)s, %(Independence)s, %(Time_Management)s, %(r_job)s) ON CONFLICT DO NOTHING;", {'name': job_title.text.strip(), 'salary': salary, 'link': link, 'company': company.text.strip(), 'type': job_type.text.strip(), 'hard_skills': hard_skills, 'location': location.text.strip(), 'Communication': keywords["Communication"], 'Customer_Service': keywords["Customer Service"], 'Leadership': keywords["Leadership"], 'Project_Management': keywords["Project Management"], 'Management': keywords["Management"], 'Analytics': keywords["Analytics"], 'Teamwork': keywords["Teamwork"], 'Problem_Solving': keywords["Problem Solving"], 'Research': keywords["Research"], 'Adaptability': keywords["Adaptability"], 'Independence': keywords["Independence"], 'Time_Management': keywords["Time Management"], 'r_job': requested_job.replace('-', '_')})
        for keyword in keywords["hard skills"]:
            cursor.execute("INSERT INTO Hard_Skills (word, frequency) VALUES (%(word)s, %(freq)s) ON CONFLICT (word) DO UPDATE SET frequency = Hard_Skills.frequency + 1 WHERE Hard_Skills.word = %(word)s;", {'word': keyword.lower(), 'freq': 1})
        for skill in ["Communication", "Customer Service", "Leadership", "Project Management", "Management", "Analytics", "Teamwork", "Problem Solving", "Research", "Adaptability", "Independence", "Time Management"]:
            cursor.execute("INSERT INTO Soft_Skills (word, total_rating) VALUES (%(word)s, %(rating)s) ON CONFLICT (word) DO UPDATE SET total_rating = Soft_Skills.total_rating + %(rating)s WHERE Soft_Skills.word = %(word)s;", {'word': skill, 'rating': keywords[skill]})

        # Add in SQL query to enter in all the keywords into the keywords table
        connection.commit()

        print("DB insertion complete!")

def scrape():
    job_title = input("What job title are you interested in? ")
    URL = "https://www.linkedin.com/jobs/search/?keywords={}&".format(job_title.replace(' ', '%20'))

    salary_yn = TerminalMenu(["Yes", "No"], title="Would you like to specify a minimum salary?")
    salary_min = ""
    if salary_yn.show() == 0:
        salary_min = TerminalMenu(["$40,000+", "$60,000+", "$80,000+", "$100,000+", "$120,000+", "$140,000+", "$160,000+", "$180,000+", "$200,000+"], multi_select=False, title="Select Desired Minimum Annual Salary")
        URL = URL + "f_SB2={}&".format(salary_min.show() + 1)

    location_yn = TerminalMenu(["Yes", "No"], title="Would you like to specify a job location?")
    job_location = ""
    if location_yn.show() == 0:
        job_location = input("Where would you like the job to be based out of? ")
        URL = URL + "location={}&".format(urllib.parse.quote_plus(job_location))
    else:
        print("No geo location")
        URL = URL + "location=&geoId=&"
    
    job_experience = TerminalMenu(["Internship", "Entry Level", "Associate", "Mid-Senior", "Director", "Executive"], multi_select=True, show_multi_select_hint=True, title="Select Desired Experience Level(s)")
    experience_levels = [str(level) for level in job_experience.show()]
    URL = URL + "f_E={}&".format('%2C'.join(experience_levels))

    type_converter = {'0': 'F', '1': 'P', '2': 'C', '3': 'T', '4': 'I', '5': 'O'}
    job_type = TerminalMenu(['Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Other'], multi_select=True, show_multi_select_hint=True, title="Select Desired Job Type(s)")
    job_types = [type_converter[str(type_)] for type_ in job_type.show()]
    URL = URL + "f_JT={}".format('%2C'.join(job_types))

    print(URL)
    process_linkedin(hrequests.get(URL, headers=headers).content.decode('utf-8'), job_title)

    force_exit = input("Time to leave ")

def display_table(table_name):
    curr_db = pd.read_sql('SELECT * FROM {}'.format(table_name), connection)
    for row in curr_db.to_string().split('\n'):
        print(row)
    holder = input("Press enter to return to the menu ")

def main():
    warnings.filterwarnings("ignore", category=UserWarning) # Pandas and psycopg2 like to complain when being used together
    os.system("clear")
    terminal_menu = TerminalMenu(["Analyze current data", "View a table's contents", "Scrape more data", "Modify the current database", "Exit"], title="What would you like to do?")
    print(ELMER_FUD)

    while True:
        print(MENU_TEXT)
        menu_entry_index = terminal_menu.show()

        if menu_entry_index == 0:
            analysis()

        elif menu_entry_index == 1:
            table_options = ["Jobs", "Companies", "Hard Skills", "Soft Skills", "Back"]
            table_names = ["jobs", "companies", "hard_skills", "soft_skills"]
            table_selection = TerminalMenu(table_options)
            table = table_selection.show()
            if table == 3:
                continue
            display_table(table_names[table])

        elif menu_entry_index == 2:
            scrape()

        elif menu_entry_index == 3:
            database_options = TerminalMenu(["Clear the current database", "Clean up the current hard skills", "Add a hard skill", "Delete an entry", "Combine hard skills", "Prune hard skills (remove all keywords with frequency of 1 or less)", "Back"], title="Select Database Operation:")
            mod_choice = database_options.show()

            if mod_choice == 0:
                drop_selection = TerminalMenu(["Yes", "No"], title="Are you sure? This cannot be undone.")
                choice = drop_selection.show()
                holder = input("Press enter to return to the menu ")
                if choice == 1:
                    continue
                cursor.execute("TRUNCATE jobs, companies, hard_skills, soft_skills CASCADE;")
                connection.commit()

            elif mod_choice == 1:
                print("One moment please...")
                clean_keywords()

            elif mod_choice == 2:
                new_keyword = input("Enter new keyword: ")
                cursor.execute("INSERT INTO hard_skills (word, frequency) VALUES (%(word)s, 0) ON CONFLICT DO NOTHING", {'word': new_keyword})
                connection.commit()
                #holder = input("Successfully added {}! ".format(new_keyword))

            elif mod_choice == 3:
                table_array = ["Jobs", "Companies", "Hard Skills", "Cancel"]
                table_options = TerminalMenu(table_array, title="Select Table to Delete From:")
                table_choice = table_options.show()

                if table_choice == 3:
                    continue

                curr_table = pd.read_sql('SELECT * FROM {}'.format(table_array[table_choice].replace(' ', '_')), connection)
                entry_select = TerminalMenu([row for row in curr_table.to_string().split('\n')[1:len(curr_table.to_string().split('\n'))]], title="Select entry to remove:")
                entry_choice = entry_select.show()
                entry_str = curr_table.iloc[entry_choice]
                print(entry_str)
                
                if table_choice == 0:
                    for soft_skill in ["Communication" ,"Customer_Service", "Project_Management" ,"Management" ,"Analytics" ,"Teamwork" ,"Problem_Solving" ,"Research", "Adaptability", "Independence", "Time_Management", "Leadership"]:
                        cursor.execute("UPDATE soft_skills SET total_rating = soft_skills.total_rating - CAST((SELECT {} FROM jobs WHERE jobs.name = %(name)s) AS int) WHERE soft_skills.word = %(s_skill)s".format(soft_skill), {'name': entry_str["name"], 's_skill': soft_skill})
                    for hard_skill in entry_str["hard_skills"]:
                        cursor.execute("UPDATE hard_skills SET frequency = hard_skills.frequency - 1 WHERE hard_skills.word = %(h_skill)s", {'h_skill': hard_skill})
                    cursor.execute("DELETE FROM jobs WHERE name = %(name)s", {'name': entry_str["name"]})

                elif table_choice == 1:
                    associated_jobs = pd.read_sql('SELECT * FROM jobs WHERE company = {}'.format(entry_str["name"]))
                    for job in associated_jobs:
                        for soft_skill in ["Communication" ,"Customer_Service", "Project_Management" ,"Management" ,"Analytics" ,"Teamwork" ,"Problem_Solving" ,"Research", "Adaptability", "Independence", "Time_Management", "Leadership"]:
                            cursor.execute("UPDATE soft_skills SET total_rating = soft_skills.total_rating - SUM({} FROM jobs WHERE jobs.company = %(company)s) WHERE soft_skills.word = %(s_skill)s".format(soft_skill), {'company': entry_str["name"], 's_skill': soft_skill})
                        for hard_skill in job["hard_skills"]:
                            cursor.execute("UPDATE hard_skills SET frequency = hard_skills.frequency - 1 WHERE hard_skills.word = %(h_skill)s", {'h_skill': hard_skill})
                    cursor.execute("DELETE FROM companies WHERE name = %(name)s", {'name': entry_str["name"]})

                else:
                    cursor.execute("UPDATE jobs SET hard_skills = array_remove(hard_skills, %(skill)s) WHERE %(skill)s = ANY(hard_skills)", {'skill': entry_str["word"]})
                    cursor.execute("DELETE FROM hard_skills WHERE word = %(skill)s", {'skill': entry_str["word"]})

                connection.commit()
                holder = input("Press enter to return to menu ")

            elif mod_choice == 4:
                curr_db = pd.read_sql('SELECT * FROM hard_skills ORDER BY word ASC', connection)
                fk_select = TerminalMenu([row for row in curr_db.to_string().split('\n')[1:len(curr_db.to_string().split('\n'))]], title="Select your base word:")
                fk_choice = fk_select.show()
                first_word = curr_db["word"][fk_choice]
                sk_select = TerminalMenu([row for row in curr_db.to_string().split('\n')[1:len(curr_db.to_string().split('\n'))]], title="Select the keywords to merge into the first:", multi_select=True, show_multi_select_hint=True)
                sk_choice = sk_select.show()
                second_word = [curr_db["word"][index] for index in sk_choice]

                for second in second_word:
                    if first_word == second_word:
                        holder = input("Cannot combine the same word ")
                        continue

                    cursor.execute("UPDATE hard_skills SET frequency = (SELECT COUNT(name) FROM jobs WHERE ( ( (%(word1)s = ANY(jobs.hard_skills) AND %(word2)s != ANY(jobs.hard_skills)) OR (%(word1)s != ANY(jobs.hard_skills) AND %(word2)s = ANY(jobs.hard_skills)) ) OR ((%(word1)s = ANY(jobs.hard_skills)) AND %(word2)s = ANY(jobs.hard_skills)) )) WHERE hard_skills.word = %(word1)s", {'word1': first_word, 'word2': second})
                    cursor.execute("DELETE FROM hard_skills WHERE word = %(word2)s", {'word2': second})
                    cursor.execute("UPDATE jobs SET hard_skills = array_append(hard_skills, %(skill1)s) WHERE %(skill2)s = ANY(hard_skills) AND %(skill1)s != ANY (hard_skills)", {'skill1': first_word, 'skill2': second})
                    cursor.execute("UPDATE jobs SET hard_skills = array_remove(hard_skills, %(skill)s) WHERE %(skill)s = ANY(hard_skills)", {'skill': second})

                    connection.commit()

                #preserve_select = TerminalMenu([first_word, second_word, "Cancel"], title="Which word do you want to preserve?")
                #preserve_choice = preserve_select.show()

                #if preserve_choice == 0:
                #    cursor.execute("UPDATE hard_skills SET frequency = (SELECT COUNT(name) FROM jobs WHERE ( ( (%(word1)s = ANY(jobs.hard_skills) AND %(word2)s != ANY(jobs.hard_skills)) OR (%(word1)s != ANY(jobs.hard_skills) AND %(word2)s = ANY(jobs.hard_skills)) ) OR ((%(word1)s = ANY(jobs.hard_skills)) AND %(word2)s = ANY(jobs.hard_skills)) )) WHERE hard_skills.word = %(word1)s", {'word1': first_word, 'word2': second_word})
                #    cursor.execute("DELETE FROM hard_skills WHERE word = %(word2)s", {'word2': second_word})
                #    cursor.execute("UPDATE jobs SET hard_skills = array_append(hard_skills, %(skill1)s) WHERE %(skill2)s = ANY(hard_skills)", {'skill1': first_word, 'skill2': second_word})
                #    cursor.execute("UPDATE jobs SET hard_skills = array_remove(hard_skills, %(skill)s) WHERE %(skill)s = ANY(hard_skills)", {'skill': second_word})

                #    connection.commit()

                #elif preserve_choice == 1:
                #    cursor.execute("UPDATE hard_skills SET frequency = (SELECT COUNT(name) FROM jobs WHERE ( ( (%(word1)s = ANY(jobs.hard_skills) AND %(word2)s != ANY(jobs.hard_skills)) OR (%(word1)s != ANY(jobs.hard_skills) AND %(word2)s = ANY(jobs.hard_skills)) ) OR ((%(word1)s = ANY(jobs.hard_skills)) AND %(word2)s = ANY(jobs.hard_skills)) )) WHERE hard_skills.word = %(word2)s", {'word1': first_word, 'word2': second_word})
                #    cursor.execute("DELETE FROM hard_skills WHERE word = %(word2)s", {'word2': first_word})
                #    cursor.execute("UPDATE jobs SET hard_skills = array_append(hard_skills, %(skill1)s) WHERE %(skill2)s = ANY(hard_skills)", {'skill1': second_word, 'skill2': first_word})
                #    cursor.execute("UPDATE jobs SET hard_skills = array_remove(hard_skills, %(skill)s) WHERE %(skill)s = ANY(hard_skills)", {'skill': first_word})

                #    connection.commit()

                #else:
                #    continue
                #for i in range(len(curr_db.to_string().split('\n'))):
                #    print(curr_db.to_string().split('\n')[i])
                #for i in curr_db.index:
                #    print(curr_db["word"][i], curr_db["frequency"][i])
                holder = input("Press enter to return to the menu ")
            elif mod_choice == 5:
                prune_table = pd.read_sql('SELECT * FROM hard_skills WHERE frequency <= 3', connection)
                for word in prune_table["word"]:
                    cursor.execute("UPDATE jobs SET hard_skills = array_remove(hard_skills, %(skill)s) WHERE %(skill)s = ANY(hard_skills)", {'skill': word})
                cursor.execute("DELETE FROM hard_skills WHERE frequency <= 3")
                connection.commit()
            else:
                continue
        else:
            break
        os.system("clear")


if __name__ == "__main__":
    main()
