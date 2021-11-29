import requests
import json
import sys
import os
import matplotlib
import sqlite3
import unittest
import csv
import matplotlib.pyplot as plt

#FIRST STEP: GO TO https://developer.spotify.com/console/get-several-episodes/?ids=77o6BIVlYM3msb4MMIL1jH,0Q86acNRm6V9GYx55SXKwf
#GENERATE A NEW TOKEN AND INSERT IT ON LINE 15

def episodes_search(id, offset,cur):
    token = 'BQDLiIY3saHvxRf1nz3eHXtmirzqyppcrYYjbqtgG4ixGJ403fTGqFzvO7o2pIAd46fW6TEbIMnWejfLzB8-uW8ZMfq8OKr-_WDR3mE2YCM8krMewy0UHwRw_-Xb6OT0p7xgJGJBUe__dovqZg'
    baseurl = 'https://api.spotify.com/v1/shows/' + id + '/episodes'
    param = {'limit':25,'offset': offset, 'access_token':token}
    response = requests.get(baseurl, params = param)
    jsonVersion = response.json()
    all_results = jsonVersion
    ids = []
    for y in all_results['items']:
        new_id = y['id']
        ids.append(new_id)
    info = []
    for x in ids:
        base_url = 'https://api.spotify.com/v1/episodes/' + x
        param = {'access_token':token}
        response = requests.get(base_url, params = param)
        jsonVersion = response.json()
        title = jsonVersion['name']
        date = jsonVersion['release_date']
        info.append((title, date))
    return info

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

def setUpEpisodes(data, cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS Spotify_Episodes (episode_id INTEGER PRIMARY KEY, name TEXT, release_date TEXT)")
    conn.commit()
    try:
        cur.execute('SELECT episode_id FROM Spotify_Episodes WHERE episode_id  = (SELECT MAX(episode_id) FROM Spotify_Episodes)')
        start = cur.fetchone()
        start = start[0]
    except:
        start= 0
    count = 1
    for x in data:
        name = x[0]
        date = x[1]
        episode_id = start+count
        #Integer primary key NOT text
        cur.execute("INSERT OR IGNORE INTO Spotify_Episodes (episode_id, name, release_date) VALUES(?,?,?)", (episode_id, name, date))
        count += 1
    conn.commit()

def createPieChart(cur): 
    # Initialize the plotcd
    fig, ax1 = plt.subplots()
    l1 = []
    
    cur.execute('SELECT * FROM Spotify_Episodes')
    cur1 = cur.fetchall()
    for row in cur1:
        l1.append(row[1])
    reg = []
    special = []
    for name in l1:
        if name.startswith('#') == True:
            reg.append(name)
        else:
            special.append(name)
    labels = 'Regular Episodes', 'Special Episodes'
    sizes = [len(reg), len(special)]
    explode = (0,0)

    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',shadow=True, startangle=90, colors = ("red","yellow"))
    plt.title('Proportion of "Special Episodes" (episodes that are not numbered)')
    ax1.axis('equal')
    plt.show()

def createBarGraph(cur,file): 
    fig, ax1 = plt.subplots()
    l1 = []
    cur.execute('SELECT * FROM Spotify_Episodes')
    cur1 = cur.fetchall()
    for row in cur1:
        l1.append(row[2])
    l2 = []
    for x in l1:
        new = x.split("-")
        if new[0] == '2020':
            l2.append(new)
    January = 0
    February = 0
    March = 0
    April = 0
    May = 0
    June = 0
    July = 0
    August = 0
    September = 0
    October = 0
    November = 0
    December = 0
    for x in l2:
        if x[1] == "01":
            January += 1
        elif x[1] == "02":
            February += 1
        elif x[1] == "03":
            March += 1
        elif x[1] == "04":
            April += 1
        elif x[1] == "05":
            May += 1
        elif x[1] == "06":
            June += 1
        elif x[1] == "07":
            July += 1
        elif x[1] == "08":
            August += 1
        elif x[1] == "09":
            September += 1
        elif x[1] == "10":
            October += 1
        elif x[1] == "11":
            November += 1
        elif x[1] == "12":
            December += 1
    
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    episodes = [January, February, March, April, May, June, July, August, September, October, November, December]
    ax1.bar(months,episodes,align='center', alpha=0.5, color='red')
    ax1.set(xlabel='Month (2020)', ylabel='Number of Episodes',
       title='Number of JRE Episodes per Month')
    ax1.set_xticklabels(months,FontSize='9')
    plt.show()

    total_zip = zip(months,episodes)
    all_data = list(total_zip)
    dir = os.path.dirname(file)
    out_file = open(os.path.join(dir, file), "w")
    with open(file) as f:
        csv_writer = csv.writer(out_file, delimiter=",", quotechar='"')
        csv_writer.writerow(["Month (2020)","Number of Episodes"])
        for x in all_data:
            csv_writer.writerow([x[0], x[1]])

def main():
    cur, conn = setUpDatabase('JRP.db')

    #SECTION 1: get data
    #to create accurate visualizations, you should gather at least 200 pieces of data (run code 8 times)
    try:
        cur.execute('SELECT episode_id FROM Spotify_Episodes WHERE episode_id  = (SELECT MAX(episode_id) FROM Spotify_Episodes)')
        start = cur.fetchone()
        start = start[0]
    except:
        start = 0
    data = episodes_search('4rOoJ6Egrf8K2IrywzwOMk', start, cur)
    setUpEpisodes(data, cur, conn)

    #SECTION 2: if you want to see calculations + visualizations, uncomment lines below.
    # createPieChart(cur)
    createBarGraph(cur, 'fileOutputEpisodes.txt')

    conn.close()


if __name__ == '__main__':
    main()