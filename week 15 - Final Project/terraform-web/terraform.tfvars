# region that our web server is going to be deployed in and the cidr ip blocks
# of the public and private subnets in the vpc that it is hosted in.
region = "us-east-1"
public_subnets = [ "10.0.1.0/24", "10.0.2.0/24" ]
private_subnets = [ "10.0.101.0/24", "10.0.102.0/24" ]