#!/usr/bin/env python

import sys, os
import boto3
from login import ec2, client
import json

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
            instance_ip = hosts[key]["ip"][i]
            create_instance_vpc(profiles[hosts[key]["profile"]], instance_ip, hostname)
            print("Instance : %s,  %s created"%(hostname, instance_ip))

    return 0

def install_salt(profiles, hosts):

    for key in hosts :
        for i in range(0, hosts[key]["number"]):
            hostname = hosts[key]["hostname"]+'-'+str(i+1)
            instance_ip = hosts[key]["ip"][i]
            key_path = KEY_REPOSITORY + 'outscale_' + profile["key"] + '.rsa'

            if hosts[key]["salt"] == "minion" :
                commands = ["sudo yum install -y https://repo.saltstack.com/yum/redhat/salt-repo-latest-2.el7.noarch.rpm",
                            "sudo yum install -y salt-minion",
                            "sudo chown centos:centos /etc/salt/minion",
                            "echo -e 'id: %s\nmaster: %s\nhash_type: sha256' > /etc/salt/minion"%(hostname.lower(),SALTMASTER),
                            "sudo systemctl enable salt-minion",
                            "sudo systemctl start salt-minion"]
                print("Connecting to : %s"%(instance_ip))
                ssh_operations.ssh_commands(instance_ip, key_path, commands)
                print("Instance : %s, %s salt-minion installed"%(hostname, instance_ip))
    return 0

def accept_salt_key(hosts):

    for host in hosts :
        hostname = hosts[host]["hostname"].lower() + '-*'
        args = ['salt-key', '-a', hostname]
        call = Popen(args, stdin=PIPE, stdout=PIPE)
        call.communicate(input='Y')
        print("Salt-key accepted for : %s"%(hostname))

    return 0


if __name__ == "__main__" :
    
    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print("Wrong number of arguments, expected :\npython create_instances.py <project name> ")

    else :
        print("Starting")
        profiles, hosts = get_hosts(sys.argv[1])
        print("Profiles and hosts loaded")
        create_hosts(profiles, hosts)
        install_salt(profiles, hosts)
        accept_salt_key(hosts)

