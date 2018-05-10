"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template
import couchdb
from visualizer import app
from collections import defaultdict,Counter


user = "admin"
password = "admin"
client = couchdb.Server("http://%s:%s@localhost:5984/" % (user, password))

def get_database(dbname,couchserver):
    if dbname in couchserver:
        db = couchserver[dbname]
    else:
        db = couchserver.create(dbname)

    return db


print("start")
sentiment = {}
stats = {}
final_stats = {}
pos, neg, neutral = {}, {}, {}


skip = 0
limit = 2000
tweet_list = [] 


docs = {}
aurin = {"selector":{"_id":{"$regex": "^"}},"fields":["properties"] ,"limit":80}

cities = []
rai = []

twitterdb = get_database('twitter',client)

sentiment = {"positive":0,"negative":0,"neutral":0}
sentiments = defaultdict(Counter)

for item in twitterdb.view('_design/city/_view/new-view',group=True):
    print(item)
    sentiments[item.key[0].lower()][item.key[1]] = item.value
print(sentiments)
for key1,value1 in sentiments.items():
    total = sum(value1.values())
    for key2,value2 in sentiments[key1].items():
        sentiments[key1][key2] = value2/total*100
print(sentiments)


@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route("/chart/")
def chart():  
    labels = ["positive", "negative", "neutral"]
    values = ["1", "2", "3"]
    # pos = 
    # neg = 
    # neutral = 
    # values = [10,9,8,7,6,4,7,8]
    # return render_template('chart.html', values=values, labels=labels)
    return render_template("chart.html", sentiments = sentiments, labels = labels)
    

@app.route("/aurin/")
def aurin():
    aurindb = get_database('aurin',client)

    for item in aurindb.view('_design/cities/_view/new-view',group=True):
        if item.key not in cities:
            cities.append(item.key)
        if item.value not in rai:
            rai.append(item.value)
    print(cities, rai)

    all_cities = ["Adelaide", "Brisbane", "Melbourne", "Perth", "Hobart"]
    pos_cities = [sentiments["adelaide"]["positive"],sentiments["brisbane"]["positive"],sentiments["melbourne"]["positive"],sentiments["perth"]["positive"], sentiments["hobart"]["positive"] ]


    labels = cities
    # pos = 
    # neg = 
    # neutral = 
    values = rai
    # return render_template('chart.html', values=values, labels=labels)
    return render_template("aurin.html", labels = labels, values = values, all_cities = all_cities, pos_cities = pos_cities)

