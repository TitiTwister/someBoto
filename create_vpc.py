#!/usr/bin/env python

import sys
import boto3
from login import ec2, client

# KEY PAIRS MUST BE PRESENTS

def create_vpc(VPC_CIDR, PROJECT_NAME):
	vpc = ec2.create_vpc(CidrBlock=VPC_CIDR)
	vpc.create_tags(Tags=[{"Key": "Name", "Value": PROJECT_NAME}])
	vpc.wait_until_available()
	print(vpc.id, "created")
	return vpc 

def create_gateway(vpc):

	int_gw = ec2.create_internet_gateway()
	vpc.attach_internet_gateway(InternetGatewayId=int_gw.id)
        ec2.create_tags(Resources = [int_gw.id], Tags=[{'Key': 'Name', 'Value': PROJECT_NAME}])
	print(int_gw.id)
	return int_gw

def create_subnet(PROJECT_NAME, DMZ_SUBNET_IP, SERVER_SUBNET_IP):
	
	dmz_subnet = vpc.create_subnet(CidrBlock=DMZ_SUBNET_IP, VpcId=vpc.id)
	server_subnet = vpc.create_subnet(CidrBlock=SERVER_SUBNET_IP, VpcId=vpc.id)
	ec2.create_tags(Resources = [dmz_subnet.id], Tags=[{'Key': 'Name', 'Value': PROJECT_NAME+'_DMZ'}])
        ec2.create_tags(Resources = [server_subnet.id], Tags=[{'Key': 'Name', 'Value': PROJECT_NAME+'_SERVER'}])
	return dmz_subnet, server_subnet

def create_nat_gw(dmz_id) :
	"""
	Create nat GW + public IP and use it

	args : dmz_id, string ex : 'subnet-6dda69e8'
    	ret : list [nat, eip]
    	"""
	
	ext_ip = client.allocate_address(
        	#Domain='vpc'|'standard',
	        #Address='string',
        	#DryRun=True|False
	    )
	ext_ip = client.describe_addresses(
		Filters=[
                	{
                	'Name': 'public-ip',
                        'Values': [ext_ip['PublicIp']]
                	}
                ]
       		)['Addresses'][0] # good part

	nat_gw = client.create_nat_gateway(
        	AllocationId=ext_ip['AllocationId'],
	        SubnetId=dmz_id
    	)['NatGateway']
	
	return ext_ip, nat_gw

def create_route_table(vpc, int_gw):

	dmz_route_table = ec2.create_route_table(
    		VpcId=vpc.id
	)

	dmz_default_route = dmz_route_table.create_route(
	    DestinationCidrBlock='0.0.0.0/0',
	    GatewayId=int_gw.id
	)
	dmz_route_table.associate_with_subnet(SubnetId=dmz_subnet.id)
	
	server_route_table = ec2.create_route_table(
	    VpcId=vpc.id
	)
	
	ext_ip, nat_gw = create_nat_gw(dmz_subnet.id)

	server_default_route = server_route_table.create_route(
	    DestinationCidrBlock='0.0.0.0/0',
	    GatewayId=nat_gw['NatGatewayId']
	)
	server_route_table.associate_with_subnet(SubnetId=server_subnet.id)
	
        ec2.create_tags(Resources = [dmz_route_table.id], Tags=[{'Key': 'Name', 'Value': PROJECT_NAME+'_DMZ'}])
        ec2.create_tags(Resources = [server_route_table.id], Tags=[{'Key': 'Name', 'Value': PROJECT_NAME+'_SERVER'}])

def create_security_group(PROJECT_NAME, vpc, DMZ_SUBNET_IP):

	for subnet in ['DMZ', 'SERVER'] :
		security_group = ec2.create_security_group(
		    GroupName=PROJECT_NAME+'_'+subnet , Description='Security rules for ' + subnet, VpcId=vpc.id)

		if subnet == 'SERVER' :
			security_group.authorize_ingress(
			    CidrIp=DMZ_SUBNET_IP[0:-4]+'254/32',
			    IpProtocol='tcp',
			    FromPort=22,
			    ToPort=22
			)


if __name__ == "__main__" :
	"""
	"""

	if len(sys.argv) < 3 or len(sys.argv) > 3:
		print("Wrong number of arguments, expected :\npython create_vpc.py <PROJECT_NAME> <VPC_CIDR/16>")

	else :
		PROJECT_NAME = sys.argv[1]
		VPC_CIDR = sys.argv[2]
		DMZ_SUBNET_IP = VPC_CIDR[:-3] + '/24'
		SERVER_SUBNET_IP = VPC_CIDR[:-6] + '100.0/24'

		vpc = create_vpc(VPC_CIDR, PROJECT_NAME)
		int_gw = create_gateway(vpc)
		dmz_subnet, server_subnet = create_subnet(PROJECT_NAME, DMZ_SUBNET_IP, SERVER_SUBNET_IP)
		create_route_table(vpc, int_gw)
		create_security_group(PROJECT_NAME, vpc, DMZ_SUBNET_IP)
