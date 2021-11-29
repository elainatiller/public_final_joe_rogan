import re
import os
import numpy as np
import sqlite3
import youtube_dl
from tabulate import tabulate
import csv
import pandas
import unittest
import matplotlib
from textwrap import wrap
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter

#set up database
def readDataFromFile(filename):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    f = open(full_path, encoding='utf-8')
    file_data = f.read()
    f.close()
    return file_data

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


#function to put 25 items from csv file to database
def uploadDataJRE(cur,conn):
    cur.execute('CREATE TABLE IF NOT EXISTS JRP (id INTEGER UNIQUE, video_id TEXT, title TEXT, views INTEGER, likes INTEGER, dislikes INTEGER, rating REAL, guestid INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS JRP_guest_count (id INTEGER PRIMARY KEY, name TEXT, apperances INTEGER)')
    # Pick up where we left off
    start = None
    #select max id (last one put in db)
    cur.execute('SELECT id FROM JRP WHERE id = (SELECT MAX(id) FROM JRP)')
    start = cur.fetchone()
    if (start!=None):
        start = start[0] + 1
    else:
        start = 1
    #select max id from guests 
    cur.execute('SELECT id FROM JRP_guest_count WHERE id = (SELECT MAX(id) FROM JRP_guest_count)')
    startguests = cur.fetchone()
    if (startguests!=None):
        startguests = startguests[0] + 1
    else:
        startguests = 1
    #open file to read data
    with open('youtube_data.csv','r') as f:
        csvreader = csv.reader(f)
        for i in range(start-1): # count and skip past rows alredy in file
            next(csvreader)
        row = next(csvreader)
        for row in csvreader:
            name = getName(row[1])
            #put name in guest id if it doesnt exist 
            if(len(name)>0):
                for x in name:
                    #try to find if they are in the db
                    cur.execute("SELECT apperances FROM JRP_guest_count WHERE name = ?",(x,))
                    apperances1= cur.fetchone()
                    if(apperances1!=None):
                        #update their apperances +=1
                        cur.execute('update JRP_guest_count set apperances = apperances + 1 where name = ?', (x,))
                    else:
                        #else they dont exist yet, add name to table
                        cur.execute("INSERT INTO JRP_guest_count(id,name,apperances) VALUES (?,?,?)", (startguests,x,1))
                        startguests=startguests+1       
            #get the id of the guest to link tables if there is only one guest
            if(len(name)==1):
                cur.execute("SELECT id FROM JRP_guest_count WHERE name = ?",(name[0],))
                guestid = cur.fetchone()[0]
            else: 
                guestid = 0
            #skip duplicate entries
            cur.execute("INSERT OR IGNORE INTO JRP (id,video_id,title,views,likes,dislikes,rating,guestid) VALUES (?,?,?,?,?,?,?,?)",(start,row[0],row[1],row[2],row[3],row[4],row[5],guestid))
            start=start + 1
            #if 25 were added break
            if (start-1) % 25 == 0:
                break
    conn.commit()

#returns list of names from titles that are in the format (Joe Rogan Experience #1567 - Donnell Rawlings & Dave Chappelle         
def getName(name):
    regex = r'^.*?#.*?(-|with)+\s*?(?P<name>.*?)(\(.*?\))?$'
    pattern = re.compile(regex)
    names = []
    try:      
        guests = re.split(',|&', pattern.match(name).group('name'))
        for person in guests:
            names.append(person.strip()) 
    except:
            pass
    return names
    
#Calculation file puts the names into youtube.txt
def printNamesPretty(cur,file):
    cur.execute('SELECT name,apperances FROM JRP_guest_count ORDER BY apperances DESC')
    names = []
    apperances = []
    for x in cur.fetchall():
        names.append(x[0])
        apperances.append(x[1])
    dir = os.path.dirname(file)
    out_file = open(os.path.join(dir, file), "w")
    with open(file) as f:
        csv_writer = csv.writer(out_file, delimiter=",", quotechar='"')
        csv_writer.writerow(["Guest","Number Apperances"])
        for x in range(len(names)):
            csv_writer.writerow([names[x], apperances[x]])

def barChart1(cur):
    # Initialize the plotcd
    fig = plt.figure(figsize=(10,4))
    ax1 = fig.add_subplot()   
    #making ax1
    l1 = dict()
    #select top 6 guests already in order 
    cur.execute('SELECT name,apperances FROM JRP_guest_count ORDER BY apperances DESC LIMIT 6 ')
    cur1 = cur.fetchall()
    for row in cur1:
        l1[row[0]]=row[1]

    people = []
    apperances=[]
    for key,value in l1.items():
        people.append(key)
        apperances.append(value)
    people = ['\n'.join(wrap(x, 16)) for x in people]
    ax1.bar(people,apperances,align='center', alpha=0.5, color='red')
    ax1.set(xlabel='Guest Name', ylabel='Apperances',
       title='8 Most Common Guests on JRP')
    ax1.set_xticklabels(people,FontSize='9')
    plt.show()

def barChart2(cur):
    fig = plt.figure(figsize=(10,4))
    ax2 = fig.add_subplot()   
    #make ax2 fist by finding 6 top episode by views
    cur.execute("SELECT views FROM JRP ORDER BY views DESC LIMIT 6")
    cur1 = cur.fetchall()
    views = []
    for x in cur1:
        views.append(x[0])
    guestname = []
    for x in views:
        cur.execute('SELECT JRP_guest_count.name FROM JRP LEFT JOIN JRP_guest_count ON JRP.guestid = JRP_guest_count.id WHERE JRP.views == ?',(x,))
        intm= cur.fetchone()
        guestname.append(intm[0])
    #if a value in 'None' due to two people on the episode, get the episode title instead 
        for x in range(len(guestname)):
            if(guestname[x]==None):
                cur.execute("SELECT title FROM JRP WHERE JRP.views == ?", (views[x],))
                title = cur.fetchone()
                title = title[0].split("- ",1)[1]
                guestname[x]=title
    # adjust views to closest whole million
    roundedviews=[]
    for x in views:
        y = str(round(x,-6))
        roundedviews.append(int(y[0:2]))
    #make ax2
    guestname = ['\n'.join(wrap(x, 16)) for x in  guestname]
    ax2.barh(guestname,roundedviews,align='center', alpha=0.5, color='red')
    ax2.set(title='Most Watched Guests of JRE')
    for index, value in enumerate(roundedviews):
        plt.text(value, index, str(value))
    ax2.legend(['Views in Millions'])
    plt.show()

def barChart3(cur):
    fig = plt.figure(figsize=(10,4))
    ax2 = fig.add_subplot()   
    #make ax2 fist by finding 6 top episode by views
    cur.execute("SELECT views FROM JRP ORDER BY views DESC LIMIT 6")
    cur1 = cur.fetchall()
    views = []
    for x in cur1:
        views.append(x[0])
    titles = []
    #get titles of the videos
    for x in views:
        cur.execute('SELECT JRP.title FROM JRP LEFT JOIN JRP_guest_count ON JRP.guestid = JRP_guest_count.id WHERE JRP.views == ?',(x,))
        intm= cur.fetchone()
        titles.append(intm[0])
    
    #get the likes and dislikes
    likes=[]
    dislikes=[]
    for x in titles:
        cur.execute('SELECT JRP.likes,JRP.dislikes FROM JRP WHERE JRP.title == ?',(x,))
        intm = cur.fetchone()
        likes.append(intm[0])
        dislikes.append(intm[1])
    N=6
    titles = ['\n'.join(wrap(x, 16)) for x in  titles]
    ind = np.arange(N)  
    width = 0.35 
    p1 = plt.bar(ind, likes, width, color = 'black')
    p2 = plt.bar(ind, dislikes, width, bottom=likes, color = 'red')
    plt.ylabel('Video Interaction')
    plt.title('Video Interactions for Top 6 Viewed JRP Youtube videos')
    plt.xticks(ind, (titles[0], titles[1], titles[2], titles[3], titles[4], titles[5]))
    #plt.yticks(np.arange(0, 81, 10))
    plt.legend((p1[0], p2[0]), ('Likes', 'Dislikes'))
    plt.show()

def barChart4(cur):
    fig = plt.figure(figsize=(10,4))
      
    #make ax2 fist by finding top 6 disliked videos
    cur.execute("SELECT dislikes,title FROM JRP ORDER BY views DESC LIMIT 6")
    cur1 = cur.fetchall()
    dislikes = []
    titles=[]
    for x in cur1:
        dislikes.append(x[0])
        titles.append(x[1])
    N=6
    titles = ['\n'.join(wrap(x, 16)) for x in  titles]
    ind = np.arange(N)  
    width = 0.35 
    p2 = plt.bar(ind, dislikes, width,  color = 'red')
    plt.ylabel('Number Dislikes')
    plt.title('Top 6 Disliked Videos on JRP Youtube')
    plt.xticks(ind, (titles[0], titles[1], titles[2], titles[3], titles[4], titles[5]))
    #plt.yticks(np.arange(0, 81, 10))
    
    plt.show()  

def pieChartMostViewedEps(cur):
    # get the most viewed eps title, like and disliked 
    # Data to plot
    cur.execute("SELECT title,likes,dislikes FROM JRP ORDER BY views DESC LIMIT 1")
    cur1 = cur.fetchall()
    
    episode = cur1[0][0]
    likes = cur1[0][1]
    dislikes = cur1[0][2]
    percLikes = likes/(likes+dislikes)
    prcDislikes = dislikes/(likes+dislikes)
    labels = ['likes (%d)'%likes,'dislikes (%d)'%dislikes]
    sizes = [percLikes,prcDislikes]
    colors = ['red','orange']
    
    # Plot
    #title1 = 'Most Viewed Episode %s likes to dislikes'%episode
    fig = plt.figure()
    ax1 = fig.add_subplot()
    plt.pie(sizes,  labels=labels, colors=colors,
        autopct='%1.1f%%', startangle=14
       )
    ax1.set(title='Most Viewed Episode %s likes to dislikes'%episode)
    #title="Most Viewed Episode %s likes to dislikes" % (episode)
    plt.axis('equal')
    plt.show()


def main():
    cur, conn = setUpDatabase('JRP.db')
    #SECTION 1 - PUT AT LEAST 200 PEOPLE BEFORE GETTING APPERANCES/GUEST NAMES BELOW 
    uploadDataJRE(cur,conn)
    printNamesPretty(cur,'youtube.txt')
  

    #GRAPHS
    barChart3(cur)
    barChart1(cur)
    barChart2(cur)
    pieChartMostViewedEps(cur)
    barChart4(cur)
   

if __name__ == '__main__':
    main()