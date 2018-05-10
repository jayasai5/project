import string,re
import couchdb

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


def process_tweet(tweet,analyzer,place):
    t = {}
    t['sentiment'] = analyzer.polarity_scores(tweet['text'])
    t['text'] = strip_all_entities(tweet['text'])
    t['id_str'] = tweet['id_str']
    if tweet['coordinates'] is not None:
        # print(tweet['coordinates'])
        t['coordinates'] = tweet["coordinates"]["coordinates"]
    if tweet['user'] is not None:
        t['user_id'] = tweet['user']['id_str']
        t['username'] = tweet['user']['name']
    t['place'] = place
    return t