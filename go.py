#!/usr/bin/env python

# Standard Imports
from __future__ import print_function
from os import chmod, makedirs, path
from shutil import rmtree
from sys import exit, stderr
from time import sleep
from urllib2 import urlopen

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
parser.add_argument("command", type=str, choices=['create', 'destroy', 'test'], help="Automated function to use.")
parser.add_argument("-L", "--label", type=str, default='default', help="The label to identify the instance of mini-project to create or interact with. Default label is 'default'")

global go_args
go_args = parser.parse_args()

# General Functions

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

def getAllResources(ses):
    resources = { 'resourceCount': 0 }
    ec2 = ses['session'].resource('ec2')

    resources['vpcs'] = ec2.vpcs.filter(Filters=[{ 'Name': 'tag:Name', 'Values': [ses['prefix'] + 'vpc'] }])
    resources['resourceCount'] += len(list(resources['vpcs']))
    
    resources['key_pairs'] = ec2.key_pairs.filter(Filters=[{ 'Name': 'key-name', 'Values': [ses['prefix'] + 'keypair'] }])
    resources['resourceCount'] += len(list(resources['key_pairs']))

    resources['gateways'] = ec2.internet_gateways.filter(Filters=[{ 'Name': 'tag:Name', 'Values': [ses['prefix'] + 'gateway'] }])
    resources['resourceCount'] += len(list(resources['gateways']))

    resources['subnets'] = ec2.subnets.filter(Filters=[{ 'Name': 'tag:Name', 'Values': [ses['prefix'] + 'subnet'] }])
    resources['resourceCount'] += len(list(resources['subnets']))

    resources['routes'] = ec2.route_tables.filter(Filters=[{ 'Name': 'tag:Name', 'Values': [ses['prefix'] + 'route'] }])
    resources['resourceCount'] += len(list(resources['routes']))

    resources['groups'] = ec2.security_groups.filter(Filters=[{ 'Name': 'tag:Name', 'Values': [ses['prefix'] + 'sg'] }])
    resources['resourceCount'] += len(list(resources['groups']))

    resources['instances'] = ec2.instances.filter(Filters=[{ 'Name': 'tag:Name', 'Values': [ses['prefix'] + 'instance'] }])
    resources['resourceCount'] += len(list(resources['instances']))

    resources['addresses'] = []
    for instance in resources['instances']:
        if instance.state['Name'] == 'terminated':
            resources['resourceCount'] -= 1
        addresses = instance.vpc_addresses.all()
        for address in addresses:
            resources['addresses'].append(address)
        resources['resourceCount'] += len(resources['addresses'])
    
    return resources

# Command Functions
def create():
    ses = getSession()
    ec2 = ses['session'].resource('ec2')

    print('Checking for existing resources for label: ' + go_args.label)
    resources = getAllResources(ses)
    if resources['resourceCount'] > 0:
        error('\nThere are existing resources for label: {0}. Either run `./go.py destroy -L {0}` or provide a different label.'.format(go_args.label))
        exit(1)

    print('Creating Key Pair')
    key_pair = ec2.create_key_pair(KeyName=ses['prefix'] + 'keypair')
    with open(ses['localdir'] + key_pair.key_name + '.pem', 'w') as pem:
        pem.write(key_pair.key_material)
        chmod(ses['localdir'] + key_pair.key_name + '.pem', 0600)

    print('Creating VPC...')
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    vpc.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'vpc' }])

    print('Creating Internet Gateway...')
    gateway = ec2.create_internet_gateway()
    gateway.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'gateway' }])
    vpc.attach_internet_gateway(InternetGatewayId=gateway.internet_gateway_id)

    print('Creating Subnet 10.0.0.0/24')
    subnet = vpc.create_subnet(CidrBlock='10.0.0.0/24')
    subnet.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'subnet' }])

    print('Setting up Routing Table...')
    routes = vpc.route_tables.all()
    for route in routes:
        route.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'route' }])
        route.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=gateway.internet_gateway_id)
        route.associate_with_subnet(SubnetId=subnet.subnet_id)

    print('Creating Security Group (open ports 22, 80, 443)...')
    sec_grp = vpc.create_security_group(GroupName=ses['prefix'] + 'sg', Description=ses['prefix'] + 'sg')
    sec_grp.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'sg' }])
    sec_grp.authorize_ingress(IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='0.0.0.0/0')
    sec_grp.authorize_ingress(IpProtocol='tcp', FromPort=80, ToPort=80, CidrIp='0.0.0.0/0')
    sec_grp.authorize_ingress(IpProtocol='tcp', FromPort=443, ToPort=443, CidrIp='0.0.0.0/0')
    
    print('Creating Instance...')
    instances = ec2.create_instances(ImageId=DEFAULT_AMI, MinCount=1, MaxCount=1, \
	KeyName=key_pair.key_name, UserData=ses['user-data'], InstanceType='t2.micro', \
	NetworkInterfaces=[{ 'DeviceIndex': 0, 'SubnetId': subnet.subnet_id, 'Groups': [sec_grp.group_id], 'AssociatePublicIpAddress': True }])
    
    print('Allocating Elastic IP...')
    eip = ec2.meta.client.allocate_address(Domain='vpc')
    vpc_address = ec2.VpcAddress(eip['AllocationId'])

    print('Waiting for Instance to Start...')
    for instance in instances:
        instance.create_tags(Tags=[{ 'Key': 'Name', 'Value': ses['prefix'] + 'instance' }])
        instance.wait_until_running()
        vpc_address.associate(InstanceId=instance.instance_id)

    print('Waiting for Web Server to Start...')
    url = 'http://{0}/index.html'.format(eip['PublicIp'])
    while 1:
        try:
            urlopen(url, timeout=15)
        except:
            print('Still Waiting...')
            sleep(15)
        else:
            break
    
    print('\n*** DONE *** \nIP of website: ' + eip['PublicIp'])


def destroy():
    ses = getSession()
    ec2 = ses['session'].resource('ec2')

    resources = getAllResources(ses)
    if resources['resourceCount'] < 1:
        error('There are no EC2 resources for the label: ' + go_args.label)
        exit(1)

    ids = []
    for key in resources:
        if key == 'resourceCount': 
            continue
        elif key == 'addresses':
            for address in resources[key]:
                ids.append(address.allocation_id)
        elif key == 'key_pairs':
            for key_pair in resources[key]:
                ids.append(key_pair.name)
        elif key == 'instances':
            for instance in resources[key]:
                if instance.state['Name'] != 'terminated':
                    ids.append(instance.id)
        else:
            for i in resources[key]:
                ids.append(i.id)

    print('\n*** The following resource ID\'s will be DESTROYED. Verify these are correct and type DESTROY to continue or anything else to cancel. ***\n')
    for i in ids:
        print(i)
    print('')
    response = raw_input('--> ')
    if response != 'DESTROY':
        exit(0)

    print('\nReleasing Elastic IP...')
    for address in resources['addresses']:
        address.association.delete()
        address.release()
    
    print('Terminating Instance...')
    for instance in resources['instances']:
        if instance.state['Name'] != 'terminated':
            instance.terminate()
            print('Waiting for instance to terminate...')
            instance.wait_until_terminated()

    print('Deleting Security Group...')
    for group in resources['groups']:
        group.delete()

    print('Deleting Subnet...')
    for subnet in resources['subnets']:
        subnet.delete()

    print('Deleting Route Table...')
    for route in resources['routes']:
        assoc = route.associations.all()
        for a in assoc:
            if not a.main: a.delete()

    for vpc in resources['vpcs']:
        print('Deleting Internet Gateway...')
        for gateway in resources['gateways']:
            vpc.detach_internet_gateway(InternetGatewayId=gateway.internet_gateway_id)
            gateway.delete()
        
        print('Deleting VPC...')
        vpc.delete()

    print('Deleting Key Pair...')
    for key_pair in resources['key_pairs']:
        key_pair.delete()
        rmtree(ses['localdir'])

    print('\n*** DONE ***')

def test():
    ses = getSession()
    r = getAllResources(ses)
    print(r['resourceCount'])

commands = { 'create': create, 'destroy': destroy, 'test': test }

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

