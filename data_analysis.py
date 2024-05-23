import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import qualifications
import math

def func(pct, total_vals):
    return "{:.1f}%\n".format(pct)

def frequency_by_year(df, categories, years):
    print(categories)
    with open("keywords.txt", 'r') as f:
        words = f.readlines()
    words = [x.strip().lower() for x in words]
    keywords = {}
    jobs_by_keywords = {}
    qualifications.generate_frequency(df, words, keywords, jobs_by_keywords)
    sorted_keywords = dict(sorted(keywords.items(), key = lambda item: item[1]))
    top_five_keys = [x for x in sorted_keywords.keys()][len(sorted_keywords.values()) - 5:len(sorted_keywords.values())]
    top_five_values = [x for x in sorted_keywords.values()][len(sorted_keywords.values()) - 5:len(sorted_keywords.values())]
    print(top_five_keys)
    print(top_five_values)
    plt.title("Top Qualifications for Jobs Asking for {} Years of Experience".format(years))
    plt.bar(top_five_keys, top_five_values)
    plt.show()
    print()

def generate_pie_chart(df):
    total_vals = 0
    total_of_vals = 0
    counts = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    mylabels = ['Not Specified', '1+ years', '2+ years', '3+ years', '4+ years', '5+ years', '6+ years', '7+ years', '8+ years', '9+ years', '10+ years']
    categories = []
    for i in range(11):
        categories.append([])
    for i in range(len(df['YOE'].tolist())):
        years = re.search(r"[1-9]{1,2}\s*[-]?\s*[1-9]{0,2}", str(df['YOE'].tolist()[i])) # years.group(0) will now contain the number of years
        if years is not None:
            if '-' in years.group(0):
                year_min = re.search(r"[1-9]{1,2}\s*[-]{1}", years.group(0)).group(0).replace('-', '').strip()
                year_max = re.search(r"[-]{1}\s*[1-9]{1,2}", years.group(0)).group(0).replace('-', '').strip()
                avg = math.floor((int(year_max.strip()) + int(year_max.strip())) / 2)
                categories[avg].append(df['ID'].tolist()[i])
                counts[avg] = counts[avg] + 1
                total_vals = total_vals + 1
                total_of_vals = total_of_vals + avg
                #for j in range(int(year_min.strip()), int(year_max.strip()) + 1):
                #    categories[j].append(df['ID'].tolist()[i])
                #    counts[j] = counts[j] + 1
                #    total_vals = total_vals + 1
                #    total_of_vals = total_of_vals + j
            else:
                counts[int(re.search(r"[1-9]{1,2}", years.group(0)).group(0).strip())] = counts[int(re.search(r"[1-9]{1,2}", years.group(0)).group(0).strip())] + 1
                categories[int(re.search(r"[1-9]{1,2}", years.group(0)).group(0).strip())].append(df['ID'].tolist()[i])
                total_vals = total_vals + 1
                total_of_vals = total_of_vals + int(re.search(r"[1-9]{1,2}", years.group(0)).group(0).strip())
        else:
            counts[0] = counts[0] + 1
    patches, texts, autotexts = plt.pie(counts[1:], startangle = -45, shadow = True, autopct = lambda pct: func(pct, total_vals), radius = 1.2,  textprops=dict(color="w")) # wedgeprops=dict(width=0.5) <== For a donut
    plt.setp(autotexts, size=8, weight="bold")
    plt.legend(patches, mylabels[1:], loc = 'center right', title = "% Breakdown by Year", bbox_to_anchor=[.15, .25])
    plt.show()
    for i in range(len(categories)):
        if len(categories[i]) > 3:
            print(i)
            frequency_by_year(df[df['ID'].isin(categories[i])], categories[i], i)