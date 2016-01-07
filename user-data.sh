#!/bin/bash

yum update -y
yum install -y git
git clone https://github.com/marty-sullivan/cloudification-mini-project.git /home/ec2-user/cloudification-mini-project
