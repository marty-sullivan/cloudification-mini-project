#!/usr/bin/env python

# Standard Imports
from __future__ import print_function
from os import makedirs, path
from shutil import rmtree
from sys import exit, stderr

# Constants

TAG_PREFIX = 'marty-mini-project-{0}-'
DIR_INSTANCE = './instance/{0}/'
DEFAULT_AMI = 'ami-6ff4bd05'

# Helpers
def warning(*objs):
    print('WARNING: ', *objs, file=stderr)

def error(*objs):
    print('ERROR: ', *objs, file=stderr)

# Test required imports
try:
    from argparse import ArgumentParser
except ImportError:
    error('ArgumentParser is not available. Ensure Python interpreter is version 2.7+')
    exit(1)

try:
    from boto3.session import Session
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    error('Python boto3 AWS SDK is not installed. Try `pip install boto3` or `easy_install boto3` (preferrably in a virtual_env).')
    exit(1)

# Parse Args
parser = ArgumentParser(description="Marty's Cloudification Mini Project")
parser.add_argument("command", type=str, choices=['create', 'destroy', 'run', 'stop', 'test'], help="Automated function to use.")
parser.add_argument("-L", "--label", type=str, default='default', help="The label to identify the instance of mini-project to create or interact with. Default label is 'default'")

global go_args
go_args = parser.parse_args()

def getSession():
    ses = { }
    ses['session'] = Session()
    ses['prefix'] = TAG_PREFIX.format(go_args.label)
    ses['localdir'] = DIR_INSTANCE.format(go_args.label)
    if not path.isdir(ses['localdir']):
        makedirs(ses['localdir'])
    with open('./user-data.sh', 'r') as ud:
        ses['user-data'] = ud.read()
    return ses

# Command Functions
def create():
    ses = getSession()
    ec2 = ses['session'].resource('ec2')
    #for i in ec2.instances.all():
    #    print(i)
    key_pair = ec2.create_key_pair(KeyName=ses['prefix'] + 'keypair')
    with open(ses['localdir'] + key_pair.key_name + '.pem', 'w') as pem:
        pem.write(key_pair.key_material)

    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    vpc.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'vpc' }])

    gateway = ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=gateway.internet_gateway_id)

    subnet = vpc.create_subnet(CidrBlock='10.0.0.0/24')
    subnet.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'subnet' }])

    route = vpc.create_route_table()
    route.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'route' }])
    route.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=gateway.internet_gateway_id)
    route.associate_with_subnet(SubnetId=subnet.subnet_id)

    sec_grp = vpc.create_security_group(GroupName=ses['prefix'] + 'sg', Description=ses['prefix'] + 'sg')
    sec_grp.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'sg' }])
    sec_grp.authorize_ingress(IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='0.0.0.0/0')
    sec_grp.authorize_ingress(IpProtocol='tcp', FromPort=80, ToPort=80, CidrIp='0.0.0.0/0')
    sec_grp.authorize_ingress(IpProtocol='tcp', FromPort=443, ToPort=443, CidrIp='0.0.0.0/0')
    
    instances = ec2.create_instances(ImageId=DEFAULT_AMI, MinCount=1, MaxCount=1, \
	KeyName=key_pair.key_name, UserData=ses['user-data'], InstanceType='t2.micro', \
	NetworkInterfaces=[{ 'DeviceIndex': 0, 'SubnetId': subnet.subnet_id, 'Groups': [sec_grp.group_id], 'AssociatePublicIpAddress': True }])
    for instance in instances:
        instance.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'instance' }])

    #ec2.create_security_group(GroupName=ses['prefix'] + 'sg'


def destroy():
    ses = getSession()
    ec2 = ses['session'].resource('ec2')
    key_pairs = ec2.key_pairs.filter(KeyNames=[ses['prefix'] + 'keypair'])
    vpcs = ec2.vpcs.filter(Filters=[{ 'Name': 'tag:Name', 'Values': [ses['prefix'] + 'vpc'] }])
    for k in key_pairs:
        k.delete()
    for vpc in vpcs:
        sec_grps = vpc.security_groups.all()
        subnets = vpc.subnets.all()
        instances = vpc.instances.all()
        routes = vpc.route_tables.all()
        gateways = vpc.internet_gateways.all()
        for instance in instances:
            instance.terminate()
            instance.wait_until_terminated()
        for sec in sec_grps:
            if sec.group_name != 'default': sec.delete()
        for subnet in subnets:
            subnet.delete()
        for route in routes:
            route.delete()
        for gateway in gateways:
            vpc.detach_internet_gateway(InternetGatewayId=gateway.internet_gateway_id)
            gateway.delete()
        
        vpc.delete()
    rmtree(ses['localdir'])
    

def run():
    print('run')

def stop():
    print('stop')

def test():
    print('test')

commands = { 'create': create, 'destroy': destroy, 'run': run, 'stop': stop, 'test': test }

# Entry

#try:
#    test_credentials()
#except NoCredentialsError:
#    error('No AWS Credentials Found. See Readme for instructions on setting up AWS credentials.')
#except ClientError as e:
#    print(e.response)



if go_args.command in commands:
    commands[go_args.command]()
else:
    error("invalid command: '{0}' (choose from {1})".format(go_args.command, sorted(commands.keys())))

