import couchdb
from twitter_utils import *
import os
import json

client = couchdb.Server("http://admin:admin@localhost:5984")
aurindb = get_database('aurin',client)
for filename in os.listdir('/root/harvester/cities'):
	with open("/root/harvester/cities/"+filename) as f:
		data = json.load(f)
		features = []
		for feature in data['features']:
			features.append(feature['properties'])
		aurindb.update(features)