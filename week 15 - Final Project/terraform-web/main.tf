terraform {

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }

  required_version = ">= 0.14.9"
}


provider "aws" {
  profile = "default"
  region  = var.region
}

# This script creates web server that publicly serves a static webpage

# Look up available AZ's in our region
data "aws_availability_zones" "available" {
  state = "available"
}

# Create a VPC
module "vpc" {
    source = "terraform-aws-modules/vpc/aws"

    name = "final-vpc"
    cidr = "10.0.0.0/16"

    azs = data.aws_availability_zones.available.names
    private_subnets = var.private_subnets
    public_subnets = var.public_subnets

    map_public_ip_on_launch = true

    enable_nat_gateway = false
    enable_vpn_gateway = false
}

# Create a web security group for application servers
# (Public HTTP Access)
module "web_server_sg" {
  source = "terraform-aws-modules/security-group/aws//modules/http-80"

  name        = "web-sg"
  description = "Security group for web-server with HTTP ports open"
  vpc_id      = module.vpc.vpc_id

  ingress_cidr_blocks = ["0.0.0.0/0"]
}

# Get the AMI for the web server
data "aws_ami_ids" "web_ami"{
  filter {
    name = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  owners = ["amazon"]
}

# Create web server
module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"

  name = "joseph-web-server"

  instance_type          = "t2.micro"
  key_name               = "vockey"
  vpc_security_group_ids = [module.web_server_sg.security_group_id]
  subnet_id              = module.vpc.public_subnets[0]
  ami                    = data.aws_ami_ids.web_ami.ids[0]

  user_data = templatefile(
    "${path.module}/init-script.sh",{
      file_content = "JOSEPH HOPWOOD"
    }
  )

}

# Give us the address to our website out
output "web_server_public_ip" {
  value = module.ec2_instance.public_ip
}