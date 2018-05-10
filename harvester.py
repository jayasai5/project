"""
Usage example:
python3 tweet_harvester.py --credFile prashant.creds
python3 tweet_harvester.py --credFile prashant.creds --couchdb_ip your_couchdb_ip_address
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
from twitter_utils import *

SLEEP_TIME = 6  # limit of 180calls / 15min for "GET search/tweets"
SHOW_DEBUG = True  # whether to show debugging printouts
RADIUS = "2km" # the search radius
COORD_INTERVAL = 0.02 # the amount to add to the lat/lon coordinates (approx 1200m in Melbourne)

twitter = []
initialUserCount = 0
credCount = 0
startTime = None
user = "admin"
password = "admin"

places = ["perth","melbourne","brisbane","sydney","adelaide","canberra","newcastle","hobart"]
place_ids = ['0118c71c0ed41109', '01864a8a64df9dc4', '004ec16c62325149', '0073b76548e5984f', '01e8a1a140ccdc5c', '01e4b0c84959d430', '6dd4aeb802da9f28', '019e32e73d7d3282']
credentials = []

def init():
    global twitter, credCount, initialUserCount, credentials,twitterUsers,client

    parser = argparse.ArgumentParser(description="This program downloads tweets from twitter for the given grid")
    parser.add_argument("--credFile",
                        type=str,
                        required=True,
                        default = 'prashant.creds',
                        help='''\ Credential file which consists of four lines per credential in the following order:
                        consumer_key
                        consumer_secret
                        access_token
                        access_token_secret
                        ...
                        ...
                        ''')

    parser.add_argument("--couchdb_ip", type=str, required=False, default = 'localhost')
    arguments = parser.parse_args()
    
    couchdb_ip = arguments.couchdb_ip
    
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
    client = couchdb.Server("http://%s:%s@%s:5984/" % (user, password,couchdb_ip))
    twitterUsers = get_database('twitter',client)
    
    print("Initial User count: ", len(twitterUsers))


# def fetch_place_ids(places):
#     global place_ids,credentials
#     auth = tweepy.OAuthHandler(credentials[4+4+0],credentials[4+4+1])
#     auth.set_access_token(credentials[4+4+2],credentials[4+4+3])
#     api = tweepy.API(auth,wait_on_rate_limit=True)
#     for place in places:
#         fetched_id = api.geo_search(query=place,granularity="city")
#         place_ids.append(fetched_id[0].id)
#         time.sleep(SLEEP_TIME / credCount)
#     print("Fetched place ids")
#     print(place_ids)

def download():
    global twitter, credCount, startTime,twitterUsers

    print("Start of downloading")
    analyzer = SentimentIntensityAnalyzer()
    # loop thru the whole city grid (lat/long) in specific intervals COORD_INTERVAL
    loopCount = 0
    while True:  # loop forever
        print("Loop number: %d" % loopCount)
        loopCount += 1
        time.sleep(SLEEP_TIME / credCount)  # avoid exceeding of API rate limits
        try:  # Twitter API crashes occasionally, so we catch this error
            print("Querying using Cred: {}, city {}".format(int(loopCount % credCount),int(loopCount % len(place_ids))))
            results = twitter[int(loopCount % credCount)]\
                        .search(q="place:%s"%place_ids[int(loopCount % len(place_ids))],
                            lang="en",
                            granularity = 'city',
                            result_type="mixed",
                            count=100)  # select only "English" tweets that are "mixed", max "100"

            for tweet in results['statuses']:
                if tweet['id_str'] not in twitterUsers:  # dont store duplicate tweets
                    processed_tweet = process_tweet(tweet,analyzer,places[int(loopCount % len(place_ids))])
                    twitterUsers[processed_tweet["id_str"]] = processed_tweet

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