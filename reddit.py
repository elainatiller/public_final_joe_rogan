from bs4 import BeautifulSoup
import requests
import re
import os
import json
import csv
import unittest
import sqlite3
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from textwrap import wrap
import datetime

#Dr. Ericson approved the .htm file to scrape Date of discussion and number of comments on that date in tuples
def getDates(filename):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), filename), 'r') as f:
        r = f.read()
    # soup = BeautifulSoup(r, 'html.parser')
    # r = requests.get('https://www.reddit.com/r/JoeRogan/search?q=general+discussion&sort=new&restrict_sr=on&t=all')
    soup = BeautifulSoup(r, 'html.parser')

    tags = soup.find_all("h3", class_ = "_eYtD2XCVieq6emjKBH3m")
    dates = []
    for x in tags:
        title = x.find('span').text.strip()
        if title.startswith("Daily General Discussion"):
            date = title.split('- ')[1]
            dates.append(date)
    
    tags2 = soup.find_all('span', class_='FHCV02u6Cp2zYL0fhQPsO')
    num_comments = []
    count = []
    num = 0
    for each in tags2:
        info = each.text.strip()
        comments = info.split(' ')[0]
        num_comments.append(comments)
        count.append(num)
        num += 1

    zip1 = zip(dates, num_comments, count)
    dates_comments = list(zip1)[:101]
    return dates_comments

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

#put 25 items into database at a time
def setUpComments(dates_comments, cur, conn):

    cur.execute("CREATE TABLE IF NOT EXISTS Popularity (discussion_id INTEGER PRIMARY KEY, dates TEXT, comments INTEGER)")

    #select max id (last one put in db)
    cur.execute('SELECT discussion_id FROM Popularity WHERE discussion_id  = (SELECT MAX(discussion_id ) FROM Popularity)')
    start = cur.fetchone()
    if (start!=None):
        start = start[0] + 1
    else:
        start = 1

    for x in dates_comments[start:start+25]:
        date = x[0]
        comments = x[1]
        discussion_id = x[2]
        cur.execute("INSERT INTO Popularity (discussion_id, dates, comments) VALUES(?, ?, ?)", (discussion_id, date, comments))
    conn.commit()

def getAverageComments(cur):
    total_months = 0
    cur.execute("SELECT dates FROM Popularity")
    info = cur.fetchall()
    for each in info:
        total_months += 1
    num_comments = 0
    cur.execute("SELECT comments FROM Popularity")
    info = cur.fetchall()
    for x in info:
        for y in x:
            num_comments += y
    average_comments = str(num_comments/total_months)
    return average_comments 

def printAverageComments(comments,file):
    dir = os.path.dirname(file)
    out_file = open(os.path.join(dir, file), "w")
    with open(file) as f:
        csv_writer = csv.writer(out_file, delimiter=",", quotechar='"')
        out_file.write('Average Number of Comments is ')
        out_file.write(comments)
    print("The average number of comments on the 100 most recent Joe Rogan Experience discussion posts on Reddit is "+comments+" comments.")

def makeVisualizations(cur):
    # Initialize the plotcd
    fig = plt.figure()
    ax1 = plt.subplot()
    width = 0.35
 
    dict1 = {}
    cur.execute("SELECT dates,comments FROM Popularity")
    info = cur.fetchall()
    for row in info:
        dict1[row[0]]=row[1]
    dates = []
    comments = []
    for key,value in dict1.items():
        key_split = key.split(',')
        month = key_split[0][0:3]
        day = key.split(' ')[1][:2]
        dates.append(month+' '+day)
        comments.append(value)
    
    dates = ['\n'.join(wrap(x, 100)) for x in dates]
    ax1.bar(dates,comments, width, color='red')
    ax1.set(xlabel='Date', ylabel='Number of Comments', title='Popularity of Podcast Dates by Comments on Reddit')
    ax1.set_xticklabels(dates,FontSize='7',rotation=70)
    plt.show()

def vizualizationByComments(cur):
#percentage of posts above 50 comments
    total_posts = 0
    cur.execute("SELECT dates FROM Popularity")
    info = cur.fetchall()
    for x in info:
        total_posts += 1

    percAbove = 0
    cur.execute("SELECT comments FROM Popularity WHERE comments >=?", (50,))
    data = cur.fetchall()
    for y in data:
        percAbove += 1
    
    percBelow = total_posts - percAbove
    labels = ["Above 50 Comments", "Below 50 comments"]
    sizes = [percAbove,percBelow]
    explode = (0, 0.1)
    colors = ['red','grey']
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, colors=colors, explode=explode, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)
    ax1.set(title='Percentage of 100 Most Recent Joe Rogan Expereince Discussion Posts on Reddit Above 50 Comments')
    ax1.axis('equal')
    plt.show()

def main():
    #run 4 times to get all 100 rows on data into database
    data = getDates('FP_reddit.htm')
    cur, conn = setUpDatabase('JRP.db')
    setUpComments(data,cur,conn)

    #to see calculations and visualizations uncomment lines below
    # average_comments = getAverageComments(cur)
    # printAverageComments(average_comments, 'reddit.txt')
    # makeVisualizations(cur)
    # vizualizationByComments(cur)

if __name__ == '__main__':
    main()