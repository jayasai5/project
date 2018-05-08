import tweepy
import argparse
import time
import couchdb
import re,string
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except Exception:
    from vaderSentiment import SentimentIntensityAnalyzer
cities = ["perth","melbourne","brisbane","sydney","adelaide","canberra","newcastle","darwin"]
def download_tweets(api):
    analyzer = SentimentIntensityAnalyzer()
    places = api.geo_search(query=city,granularity="city")
    place_id = places[0].id
    for tweet in tweepy.Cursor(api.search,q="place:%s"%place_id,lang="en").items(): 
        if tweet.id_str not in tweetdb:
            processed_tweet = process_tweet(tweet,analyzer)
            tweetdb[processed_tweet["id_str"]] = processed_tweet

def process_tweet(tweet,analyzer):
    t = {}
    t['sentiment'] = analyzer.polarity_scores(tweet.text)
    t['text'] = strip_all_entities(tweet.text)
    t['id_str'] = tweet.id_str
    if tweet.coordinates is not None:
        print(tweet.coordinates)
        t['coordinates'] = tweet.coordinates["coordinates"]
    if tweet.place is not None:
        t['place'] = tweet.place.name
    if tweet.user is not None:
        t['user_id'] = tweet.user.id_str
        t['username'] = tweet.user.name
    return t

def get_auth(credentials):
    auth = tweepy.OAuthHandler(credentials[0],credentials[1])
    auth.set_access_token(credentials[2],credentials[3])
    return auth

def get_database(dbname,couchserver):
    if dbname in couchserver:
        db = couchserver[dbname]
    else:
        db = couchserver.create(dbname)

    return db
            

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

def init():
    global city,tweetdb,client
    user = "admin"
    password = "admin"
    client = couchdb.Server("http://%s:%s@localhost:5984/" % (user, password))
    tweetdb = get_database('twitter',client)
    parser = argparse.ArgumentParser(description="This program downloads tweets from twitter for a given city")
    parser.add_argument("--cred_file",
                        type=str,
                        required=True,
                        help='''\ Credential file which consists of four lines in the following order:
                        consumer_key
                        consumer_secret
                        access_token
                        access_token_secret
                        ...
                        ...
                        ''')
    parser.add_argument("--index",
                        type=str,
                        required=True,
                        help="machine index to pick cities")
    arguments = parser.parse_args()
    city = cities[int(arguments.index)] 
    credentials = []
    with open(arguments.cred_file) as fr:
        lines = 0
        for l in fr:
            lines += 1
            credentials.append(l.strip())
        if lines % 4 != 0:
            raise Exception("Invalid Credentials, each credential must consists of 4 lines")
    auth = get_auth(credentials[:4])
    api = tweepy.API(auth,wait_on_rate_limit=True)
    download_tweets(api)


def main():
    init()

if __name__ == '__main__':
    main()
