"""
Usage example:
For melbourne.
python3 tweet_harvester.py --credFile prashant.creds --minLat -37.857366 --maxLat -37.767133 --minLong 144.892953 --maxLong 145.010027
For Australia Quadrant-1:
python3 tweet_harvester.py --credFile prashant.creds --minLat -43.6345972634 --maxLat -10.6681857235 --minLong 113.338953078 --maxLong 153.569469029


"""
try:
    import ujson as json
except ImportError:
    import json

import time
import datetime
import argparse
from twython import Twython, TwythonError
import os
import couchdb
from numpy import arange
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except Exception:
    from vaderSentiment import SentimentIntensityAnalyzer
import re,string


SLEEP_TIME = 5  # limit of 180calls / 15min for "GET search/tweets"
SHOW_DEBUG = True  # whether to show debugging printouts
RADIUS = "1km" # the search radius
COORD_INTERVAL = 0.01 # the amount to add to the lat/lon coordinates (approx 1200m in Melbourne)

twitter = []
initialUserCount = 0
credCount = 0
startTime = None
user = "admin"
password = "admin"
client = couchdb.Server("http://%s:%s@localhost:5984/" % (user, password))
minLat = None
maxLat = None
minLong = None
maxLong = None


def get_database(dbname,couchserver):
    if dbname in couchserver:
        db = couchserver[dbname]
    else:
        db = couchserver.create(dbname)

    return db

twitterUsers = get_database('twitter',client)

def init():
    global twitter, credCount, initialUserCount, minLat, maxLat, minLong, maxLong

    parser = argparse.ArgumentParser(description="This program downloads tweets from twitter for the given grid")
    parser.add_argument("--credFile",
                        type=str,
                        required=True,
                        help='''\ Credential file which consists of four lines per credential in the following order:
                        consumer_key
                        consumer_secret
                        access_token
                        access_token_secret
                        ...
                        ...
                        ''')

    parser.add_argument("--minLat", type=str, required=False, help="minLat: The minimum latitude coordinates to start searching from, e.g., -37.813741")
    parser.add_argument("--maxLat", type=str, required=False, help="maxLat: The maximum latitude coordinates to search until, e.g., -37.813741")
    parser.add_argument("--minLong", type=str, required=False, help="minLong: The minimum longitude coordinates to start searching from, e.g., 144.963200")
    parser.add_argument("--maxLong", type=str, required=False, help="maxLong: The maximum longitude coordinates to search until, e.g., 144.963200")
    arguments = parser.parse_args()
    
    minLat = float(arguments.minLat)
    maxLat = float(arguments.maxLat)
    minLong = float(arguments.minLong)
    maxLong = float(arguments.maxLong)

    print("Lat Long {} {} {} {}".format(minLat, minLong, maxLat, maxLong ))

    credentials = []
    with open(arguments.credFile) as fr:
        lines = 0
        for l in fr:
            lines += 1
            credentials.append(l.strip())
        if lines % 4 != 0:
            raise Exception("Invalid Credentials, each credential must consists of 4 lines")

    while credCount < lines:
        twitter.append(Twython(credentials[credCount], credentials[credCount + 1], credentials[credCount + 2],
                               credentials[credCount + 3]))
        credCount += 4

    credCount /= 4

    print("Initial User count: ", len(twitterUsers))


def strip_links(text):
    link_regex    = re.compile('((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)', re.DOTALL)
    links         = re.findall(link_regex, text)
    for link in links:
        text = text.replace(link[0], ', ')    
    return text

def strip_all_entities(text):
    entity_prefixes = ['@','#']
    for separator in  string.punctuation:
        if separator not in entity_prefixes :
            text = text.replace(separator,' ')
    words = []
    for word in text.split():
        word = word.strip()
        if word:
            if word[0] not in entity_prefixes:
                words.append(word)
    return ' '.join(words)

def download():
    global twitter, credCount, startTime, minLat, maxLat, minLong, maxLong

    print("Start of downloading")
    analyzer = SentimentIntensityAnalyzer()
    # loop thru the whole city grid (lat/long) in specific intervals COORD_INTERVAL
    loopCount = 0
    while True:  # loop forever
        print(minLat,maxLat,COORD_INTERVAL)
        for lat in arange(minLat, maxLat, COORD_INTERVAL):
            for lon in arange(minLong, maxLong, COORD_INTERVAL):
                geoSearch = str(lat) + "," + str(lon) + "," + RADIUS # geolocation search code for Twitter API 
                print("Loop number: %d" % loopCount)
                loopCount += 1
                time.sleep(SLEEP_TIME / credCount)  # avoid exceeding of API rate limits
                try:  # Twitter API crashes occasionally, so we catch this error
                    print("Querying using Cred: {}".format(int(loopCount % credCount)))
                    results = twitter[int(loopCount % credCount)]\
                        .search(geocode=geoSearch,
                                lang="en",
                                result_type="recent",
                                count=100)  # select only "English" tweets that are "recent", max "100"

                    for tweet in results['statuses']:
                        if tweet['id_str'] not in twitterUsers:  # dont store duplicate tweets
                            tweet['sentiment'] = analyzer.polarity_scores(tweet['text'])
                            # Clean Tweets here
                            tweet['clean_tweet'] = strip_all_entities(tweet['text'])
                            twitterUsers[tweet['id_str']] = tweet

                except TwythonError as genError:
                    print("Twitter error: %s" % genError)
                    print("Sleeping for {} minutes".format(15 / credCount))
                    time.sleep(15 * 60 / credCount)  # sleep for 15 min, then try the API again

                if loopCount % (SLEEP_TIME * 3) == 0:
                    print("\n------------Running time statistics------------")
                    endTime = datetime.datetime.now()
                    print("New user data count: %s" % (len(twitterUsers) - initialUserCount))
                    print("Start time:          %s" % str(startTime))
                    print("Time elapsed:        %s" % (endTime - startTime))


def main():
    global startTime
    startTime = datetime.datetime.now()
    print("Start time:    %s" % str(startTime))
    init()
    download()

if __name__ == "__main__":
    main()
