#!/usr/bin/env python

# Standard Imports
from __future__ import print_function
from sys import exit, stderr

# Constants

EC2_AMI = ''

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
    import boto3
except ImportError:
    error('Python boto3 AWS SDK is not installed. Try `pip install boto3`')
    exit(1)

# Parse Args
global args
parser = ArgumentParser(description="Marty's Cloudification Mini Project")
parser.add_argument("command", type=str, choices=['create', 'destroy', 'run', 'stop', 'test'], help="Automated function to use.")
args = parser.parse_args()

# Functions
def create():
    pass

def destroy():
    pass

def run():
    pass

def stop():
    pass

def test():
    pass

# Entry


