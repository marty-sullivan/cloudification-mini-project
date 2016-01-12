# Marty's Cloudification Mini Project

### Summary

A Python script to create, destroy and/or test a static website on AWS EC2 using an Infrastructure as Code approach. Having a black hole in my head in terms of the VPC stack, I decided to dive in and have this script provision the whole thing to obtain a better understanding. The script will create a VPC, Internet Gateway, Subnet, Route Table, Security Group, Key Pair, Elastic IP and EC2 Instance. The instance is initalized with the most recent Amazon ECS-Optimized AMI; "user-data.sh" is passed to the instance on launch. The User Data script builds a Docker image and, in turn, runs a container serving a static webpage via Apache2. 

### Preparation

The following are needed to use this script:

1. Python 2.7+
2. Python Boto 3 Module (AWS SDK)
3. AWS Account w/ privileged IAM user
4. AWS CLI Credentials Configured
5. This Git Repo

See the following Quickstart Guide for getting Boto 3 installed and AWS credentials configured:

http://boto3.readthedocs.org/en/latest/guide/quickstart.html

### Commands

Everything is run from the go.py script.

    ./go.py create -L myLabel
    
This command will create a new stack that will run the static web page. All the created resources will be tagged according to the provided label. It will output the Elastic IP address of the EC2 instance running the webpage once the command completes.

    ./go.py destroy -L myLabel
    
This command will enumerate any existing resources for the provided label. It will present the ID's of all the resources to be destroyed and give the user a chance to verify before committing to the destruction. 

    ./go.py test -L myLabel
    
If resources with the provided label exist, this command will test that the related webpage has the expected content "Cloudification Rocks!" in order to verify that the infrastructure is operational.
