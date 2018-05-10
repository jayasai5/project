
import json
import couchdb
from twitter_utils import *


client2 = couchdb.Server("http://admin:admin@localhost:5984")
twitterUsers = get_database('twitter',client2)

with open("backup") as f:
	data = json.load(f)
tweets = []
for item in data['rows']:
	if len(tweets)>10000:
		twitterUsers.update(tweets)
		tweets =[]
	tweets.append(item['doc'])