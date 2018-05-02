# -*- coding: utf-8 -*-
"""
Created on Sun Apr 29 09:33:19 2018

@author: jayanth
"""

import argparse
from novaclient import client
from keystoneauth1 import loading,session
from cinderclient import client as cclient
from neutronclient.v2_0 import client as nclient
#add options to the command line argument parser
zones = ["QRIScloud","auckland","melbourne-np","melbourne-qh2","monash-03","NCI","tasmania-s","swinburne","intersect","sa","monash-02","tasmania","monash-01"]
parser = argparse.ArgumentParser(description = "Deploy the application on necter which can scale to the given number of instances.")
parser.add_argument('-n','--instances',type = int, help = 'number of instances to deploy the application on(Optional)',default = 4)
parser.add_argument('-k','--apikey',help = 'openstack api key for connecting to nectar')
parser.add_argument('-a','--authurl',help = 'use this option to specify an authentication url(Optional)',default = "https://keystone.rc.nectar.org.au:5000/v2.0/")
parser.add_argument('-i','--projectid',help = 'specify the project id for authentication(Optional)',default = '1e8ec98ca2154094bdf58166999fc789')
parser.add_argument('-u','--username',help = 'institutional login username for authentication')
parser.add_argument('-e','--keypairname',help = 'specify the name of the keypair for access to instances(Optional)',default = 'my_key_pair')
parser.add_argument('-z','--zone',help = 'the availabilty zone to deploy the machines in(Optional)',default = 'melbourne-qh2',choices = zones)
parser.add_argument('-v','--storagevolume',help = 'the total amount of storage to use across all instances',default="250",type = int)
args = parser.parse_args()


#parse the innput arguments
no_of_instances = args.instances
apikey = args.apikey
authurl = args.authurl
projectid = args.projectid
username = args.username
keypair_name = args.keypairname
zone = args.zone
volume = args.storagevolume
#get storage for each instance
instance_storage = int(volume/no_of_instances)

#get the loader
loader = loading.get_plugin_loader('password')

print("Creating authentication")
#add authenticaation to the loader
auth = loader.load_from_options(auth_url=authurl, username=username, password=apikey, project_id=projectid)

print("Creating Session")
#create a session using the settings above
sess = session.Session(auth = auth)

print("Creating Security Groups")
neutron = nclient.Client(session = sess)
group = neutron.create_security_group({'security_group':{'tenant_id':projectid,'name':'couchdb','description':'security group from couchdb setup'}})
group_id = group["security_group"]["id"]
neutron.create_security_group_rule({'security_group':'couchdb','security_group_rule':{'security_group_id':group_id,'direction':'ingress','ethertype':'IPv4','protocol':'TCP','port_range_min':'1','port_range_max':'9999','remote_ip_prefix':'0.0.0.0/0'}})
neutron.create_security_group_rule({'security_group':'couchdb','security_group_rule':{'security_group_id':group_id,'direction':'egress','ethertype':'IPv4','protocol':'TCP','port_range_min':'1','port_range_max':'9999','remote_ip_prefix':'0.0.0.0/0'}})
neutron.create_security_group_rule({'security_group':'couchdb','security_group_rule':{'security_group_id':group_id,'direction':'ingress','ethertype':'IPv4','protocol':'TCP','port_range_min':'5984','port_range_max':'5984','remote_ip_prefix':'0.0.0.0/0'}})
group = neutron.create_security_group({'security_group':{'tenant_id':projectid,'name':'ssh','description':'security group from ssh '}})
group_id = group["security_group"]["id"]
neutron.create_security_group_rule({'security_group':'ssh','security_group_rule':{'security_group_id':group_id,'direction':'ingress','ethertype':'IPv4','protocol':'TCP','port_range_min':'22','port_range_max':'22','remote_ip_prefix':'0.0.0.0/0'}})

print("Creating nova client for instance creation and editing")
#create a nova client
nova = client.Client("2",session = sess)

print("Creating cinder client for volume creation")
#create a cinder client
cinder = cclient.Client("3",session = sess)

print("Creating keypair for deployment")
#create a key_pair for access to servers
try:
    keypair = nova.keypairs.create(name = keypair_name)
except:
    print("keypair exists !! using existing keypair")
    keypair = nova.keypairs.get(keypair_name)

print("Creating instances and volumes")
server_names = []
volume_names = []
#use nova client to launch servers
for i in range(no_of_instances):
    server_name = "cc_instance_"+str(i+1)
    server_names.append(server_name)
    volume_name = "cc_volume_"+str(i+1)
    volume_names.append(volume_name)
    image = '0f72065c-2937-4ece-b3d5-424808ca7cdf' #code for ubuntu 16.04(Xenial)  
    flavor = '1' # code for m1.medium
    security_groups = ['couchdb','default','ssh']
    availability_zone = zone
    nova.servers.create(server_name,image,flavor,security_groups = security_groups,key_name = keypair_name,availability_zone = zone)
    cinder.volumes.create(str(instance_storage),name = volume_name,availability_zone = zone)

building = True
server_ids = []
volume_ids = []
server_ips = []
print("waiting for servers to boot up....")
while(building):
    servers = nova.servers.list()
    building = False
    for server in servers:
        server_ids.append(server.id)
        server_ips.append(server.accessIPv4)
        if server.name in server_names and server.status != "ACTIVE":
            building = True
            server_ids = []
            break;
    

creating = True
print("waiting for volumes to be created....")
while(creating):
    volumes = cinder.volumes.list()
    creating = False
    for volume in volumes:
        volume_ids.append(volume.id)
        if volume.name in volume_names and volume.status != "available":
            creating = True
            volume_ids = []
            break;
            
#print(server_ids,volume_ids)
print("attaching volumes")
for i in range(no_of_instances):
    nova.volumes.create_server_volume(server_ids[i],volume_ids[i])
print("done")