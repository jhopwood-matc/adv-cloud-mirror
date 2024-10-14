#!/usr/bin/env python3

'''
Author: Joseph Hopwood
Description: Output a report of a specific or all security groups. Focused on
identifying security groups with internet access that is too open.
'''

import boto3
import argparse

# Let's create a parser to handle the arguments passed ot the script.
# Let's also add some helpful about metadata.
parser: argparse.ArgumentParser = argparse.ArgumentParser(
    prog="SG Vulnerability Checker",
)

# Let's add the parameter to give check a security group individually.
parser.add_argument(
    "-s", "--security-group",
    type=str,
    help="Name of the security group in AWS",
    dest="sg",
    )

# ...registering the arguments passed ...
args = parser.parse_args()

# Let's get our low level client to make API calls. Nice.
client_ec2 = boto3.client('ec2')

# Now. let's either make an API call to get information about a SINGLE security
# group given that the user passed in an argument for "--security-group" into
# the script, or make an API call to give use back information on EVERY security
# group if that was not specified.

response: dict = {}

# SINGLE - API call
if args.sg:
    response = client_ec2.describe_security_groups(
        GroupNames=[
            args.sg,
        ],
    )
# EVERY - API call
else:
    response = client_ec2.describe_security_groups()

try:
    # Let's grab the list of security groups from the response so we can parse
    # through it to find the information that we want.
    security_groups: list = response["SecurityGroups"]

    # Let's take a closer look at each security group so that we can check
    # the rules in each one..
    for group in security_groups:

        # Okay, let's crack open the rules and look inside.
        for inbound_rule in group["IpPermissions"]:

            # We are going to yank out a list of the IP ranges associated with
            # each rule. Let's initialize it.
            ip_ranges: list = []

            # We are also going to create this flag that is going to flip if
            # any of the IP's associated with the rule are 0.0.0.0/0 (anywhere)
            too_open = False

            # Okay, let's have a look at each of the IP ranges
            for ip_range in inbound_rule["IpRanges"]:

                # Let's add each IP to that list we made above
                ip_ranges.append(ip_range["CidrIp"])

                # Let's flag it if it is too open 
                if ip_range["CidrIp"] == "0.0.0.0/0":
                    too_open = True

            # Now we can print the name of the group that the rule is a part of.
            print(f"\nSecurity Group Name: {group['GroupName']}")

            # And we can print the associated IP ranges in of the rule
            print("IP Ranges:")
            for ipr in ip_ranges:
                print(f"  - {ipr}")

            # Let's also print the ports
            print(f"From Port: {inbound_rule['FromPort']}")
            print(f"To Port: {inbound_rule['ToPort']}")

            # Finally --a warning message if it was flagged for being too open.
            if too_open:
                print("WARNING: Open to the public internet!")

# Some security groups ('default' im looking at you) dont have all these fields,
# let's catch that possible error
except KeyError:
    pass

# this separates the printed result from the consoles next stdin
print("\n")