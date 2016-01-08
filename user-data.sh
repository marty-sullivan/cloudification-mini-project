#!/bin/bash

yum update -y
yum install -y git
git clone https://github.com/marty-sullivan/cloudification-mini-project.git /home/ec2-user/cloudification-mini-project
(cd /home/ec2-user/cloudification-mini-project/docker; docker build -t cloudification-rocks /home/ec2-user/cloudification-mini-project/docker)
docker run -d --restart=always --name cloudification-rocks-live -p 80:80 cloudification-rocks

