#!/usr/bin/env python

import sys, os
import boto3
from login import ec2, client
import json
import ssh_operations

SALTMASTER = 'x.x.x.x'
KEY_REPOSITORY = '/etc/salt/key/'

def get_hosts(project):
    
    files = ['profiles', 'hosts']
    res = []
    dirname = os.path.dirname(os.path.realpath('__file__'))

    for el in files:

        current_file  = dirname + '/' + el + '/' + project + '.json'
    
        with open(current_file) as f:
            res.append(json.load(f))
    
    return res[0], res[1]


def create_instance_vpc(profile, ip_addr, hostname):
    instances = ec2.create_instances(
                            ImageId= profile["ami"], 
                            InstanceType= profile["type"], 
                            MaxCount=1, 
                            MinCount=1,
                            KeyName= profile["key"],
                            NetworkInterfaces=[{
                                        'SubnetId': profile["vpc"], 
                                        'DeviceIndex': 0, 
                                        'AssociatePublicIpAddress': True, 
                                        'Groups': [profile["sg"]],
                                        'PrivateIpAddress': ip_addr,
                                        }]

                            )
    instances[0].wait_until_running()
    ec2.create_tags(Resources = [instances[0].id], Tags=[{'Key': 'Name', 'Value': hostname}])

def create_hosts(profiles, hosts):
    
    for key in hosts :
        for i in range(0, hosts[key]["number"]):
            hostname = hosts[key]["hostname"]+'-'+str(i+1)

            create_instance_vpc(profiles[hosts[key]["profile"]], hosts[key]["ip"][i], hostname)
            print("Instance : %s created"%(hosts[key]["ip"][i]))
            if hosts[key]["salt"] == "minion" :
                ssh_operations.ssh_commands(hosts[key]["ip"][i], 
                                            KEY_REPOSITORY + 'outscale_' + profiles[hosts[key]["profile"]["key"], 
                                            ['hash_type: sha256',
                                                'sudo yum install -y salt-minion',
                                                 "echo -e 'id: %S\nmaster: %s' > /etc/salt/minion"%(hostname.lower(), 
                                            SALTMASTER)])
                print("Instance : %s salt-minion installed"%(hosts[key]["ip"][i]))
    return 0

if __name__ == "__main__" :
    
    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print("Wrong number of arguments, expected :\npython create_instances.py <project name> ")

    else :
        profiles, hosts = get_hosts(sys.argv[1])
        create_hosts(profiles, hosts)
