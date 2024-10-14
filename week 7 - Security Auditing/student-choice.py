#!/usr/bin/env python3

'''
Author: Joseph Hopwood
Description: Describe VPCs and their attached subnets to notify the user if the
network lacks High Availability.

It can either return info about a specific VPC, or all VPCs.
'''

import boto3
import argparse

# Let's create a parser to handle the arguments passed ot the script.
# Let's also add some helpful about metadata.
parser: argparse.ArgumentParser = argparse.ArgumentParser(
    prog="Network High Availability Checker",
)

# Let's add the parameter to give check a VPC individually.
parser.add_argument(
    "-n", "--vpc-name",
    type=str,
    help="Name of the VPC in aws",
    dest="vpc_name",
    )

# ...registering the arguments passed ...
args = parser.parse_args()

# Let's begin by creating the low level client to interact with ec2
client_ec2 = boto3.client("ec2")

# In order ot determine whether or not a network can host highly available
# infrastructure, we need to see if it has enough subnets. Specifically, they
# they need to be subnets in different Availability Zones.

# Let's begin by obtaining the networks we want to check. This script will
# either do all networks on the account, or a single one that was queried by
# a name that was passed in as an argument when the script was executed.

response: dict = {}

# For a single, named, VPC
if args.vpc_name:
    response = client_ec2.describe_vpcs(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    args.vpc_name,
                ]
            },
        ],
    )

# For all VPCs
else:
    response = client_ec2.describe_vpcs()

# From this response, we are going to take out the information from it that we
# want.

# - VpcId: The user may want this, but we re also going to use it to get the 
#       list of subnets that are associated with it.
# - Name: This is helpful so the user can identify what vpc it is
# - CidrIp: I think this is also relevant information.

# Then, we are going to organize it nicely and put it in a dictionary. Then we
# can populate the "subnets" value when we query them.
"""
[
    {
        "id" : str
        "name" : str,
        "cidr" : str,
        "subnets" : [
            {
                "id" : str,
                "name" : str,
                "az" : str,
                "cidr" : str
            },
            ...
        ]
    },
    ...
[
"""
# Let's create the collection of our vpc information:
vpc_list: list = []




# Let's create a function that will give us the information that we want.
def get_vpc_info(vpc: dict) -> dict:
    """_Get key info from a VPC._

    Args:
        vpc (dict): _VPC metadata that was returned
            from a `EC2.client.describe_vpcs()` call --located within 
            `response["Vpcs"]`._

    Returns:
        dict: _Key information about a VPC. the "subnet" value is always empty.
            See get_associated_subnets_info()_  
        `
        {  `<br>`
        "id" : str,  `<br>`
        "name" : str,  `<br>`
        "cidr" : str,  `<br>`
        "subnets" : list  `<br>`
        }
        `

    """

    id: str = vpc["VpcId"]
    name: str = "-"
    cidr: str = vpc["CidrBlock"]

    # Sometimes they don't have tags. We need to catch this error and stick with
    # the default "-"
    try:
        for tag in vpc["Tags"]:
            if tag["Key"] == "Name":
                name = tag["Value"]
    except KeyError:
        pass

    return {
        "id" : id,
        "name" : name,
        "cidr" : cidr,
        "subnets" : []
    }




# Okay, now let's use it.
# Let's add the info for all of the vpcs returned in the response.
for vpc in response["Vpcs"]:
    vpc_list.append(get_vpc_info(vpc))

# Now that we have the ID(s) of the VPC(s), we can request a list of all the
# associated subnets for each VPC. Then we can take the info we want.

# - Subnet ID: if they are un-named, we need to know the IDs
# - Name: For the user to know which subnet is which
# - Availability Zone: So we can determine if the vpc supports high availability
# - CidrIp: Relevant information




# Let's make a function for that.
def get_associated_subnets_info(ec2_client, vpc_id: str) -> list[dict]:
    """_Get a list of key information on each subnet in a VPC._

    Args:
        ec2_client (_type_): _An instance of a low level client with the EC2
            service._
        vpc_id (str): _The ARN of the VPC that you want to get the subnets and
            the information of._

    Returns:
        list[dict]: _A list of dictionaries each containing key information
            about a subnet._

        `
        {  `<br>`
            "id" :  str,  `<br>`
            "name" : str,  `<br>`
            "az" : str,  `<br>`
            "cidr" : str,  `<br>`
        }
        `
        
    """
    # This is be our return value
    list_of_subnets: list[dict] = []
    
    # Let's get the list of subnets associated with our VPC
    response = ec2_client.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            },
        ],
    )

    # Now, let's extract the key info, package it in a dict, and add it to the
    # list of subnets
    for subnet in response["Subnets"]:

        name = "-"

        # Sometimes they don't have tags. We need to catch this error and stick 
        # with the default "-"
        try:
            for tag in subnet["Tags"]:
                if tag["Key"] == "Name":
                    name = tag["Value"]
        except KeyError:
            pass

        list_of_subnets.append(
            {
                "id" :  subnet['SubnetId'],
                "name" : name,
                "az" : subnet['AvailabilityZone'],
                "cidr" : subnet['CidrBlock'],
            }
        )

    return list_of_subnets




# Now, we can use that function to fill in the subnet information in our VPCs
# in our list of VPCs
for vpc in vpc_list:
    vpc["subnets"] = get_associated_subnets_info(client_ec2, vpc["id"])

# print(vpc_list)

# Now that we have all the information we want, we can go through and check each
# VPC to see if they are highly available. For this, our criteria is just that
# there are **At least 2 subnets** and the 2 subnets are **in different AZs**.

# This is easy enough, because all we have to do is make sure that the count of
# subnets is above two, and that the az's end with unique characters.

# Let's divide these into two checks, and if the VPC doesn't pass both, we will
# flag it and let the user know.

# Let's create a list that will hold the VPC IDs of flagged VPCs
flagged_vpcs_list: list[str] = []

# Let's start checking!
for vpc in vpc_list:

    # Let's do check one: **At least 2 subnets**
    if len(vpc["subnets"]) >= 2:
        
    # We are only gonna do check two if one passes, it's probably not
    # optimal to have nested ifs like this for checks, but we only have two
    # so this works.

    # Okay, and let's do check two: **in different AZs**

        # This list will keep track of the unique chars at the end of the
        # subnets AZ names
        unique_chars: list[str] = []

        for subnet in vpc["subnets"]:
            if subnet["az"][-1] not in unique_chars:
                unique_chars.append(subnet["az"][-1])

        if len(unique_chars) >= 2:
            pass

        else:
            flagged_vpcs_list.append(vpc["id"])

    else:
        flagged_vpcs_list.append(vpc["id"])
    
    
# Okay, now that we have flagged/passed all the VPCs, we can go ahead and print
# them out for the user to see.
for vpc in vpc_list:
    print("\n")
    print(f"Name: {vpc['name']}")
    print(f"ARN: {vpc['id']}")
    print(f"IP Cidr: {vpc['cidr']}")
    print("Subnets:")
    for subnet in vpc["subnets"]:
        print(f"  - Name: {subnet['name']}")
        print(f"    ARN: {subnet['id']}")
        print(f"    AZ: {subnet['az']}")
        print(f"    IP Cidr: {subnet['cidr']}")
        
    # Let's attach a warning to the flagged VPCs
    if vpc["id"] in flagged_vpcs_list:
        print("WARNING: Network is not Highly Available!")
    print("\n")