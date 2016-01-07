#!/usr/bin/env python

# Standard Imports
from __future__ import print_function
from sys import exit, stderr

# Constants

TAG_PREFIX = 'marty-mini-project-'

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

global go_args
go_args = parser.parse_args()

# Init AWS Session
global session
session = Session()

# AWS Functions

#def test_credentials():
#    ec2 = session.resource('ec2')
#    ec2.create_key_pair(DryRun=True, KeyName='blah')
    

# Command Functions
def create():
    print('create')

def destroy():
    print('destroy')

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

