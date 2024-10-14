'''
Author: Joseph Hopwood
Description: Output a report of all IAM roles created in the last 90
days. Focused on identifying managed and unmanaged policies associated with 
each role.
'''

import datetime
import botocore.exceptions
import pytz

import boto3
import botocore

# Let's get the date and time of this moment 90 days ago
# We will use this later to filter the results of IAM roles on our account.
now: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())
ninety_days_ago: datetime.datetime = now - datetime.timedelta(days=90)

# IAM client
client_iam = boto3.client('iam')

# Get a list of all the IAM roles on the account
response_roles: dict = client_iam.list_roles()

# Let's identify and organize the data that we want to get,
role_metadata: list = []
# It will be populated with dictionaries formatted as follows
###########################################################
# {
#     "RoleName" : str,
#     "CreateDate" : datetime.datetime,
#     "ManagedPolicies" : [
#         str,
#     ],
#     "UnmanagedPolicies" : [
#         str
#     ],
# }
###########################################################

# Let's go through all the roles that it handed back, filter for the ones that
# we want, and then extract the metadata from them that we are looking for.
for role in response_roles["Roles"]:
    
    # First, let's find out when the roles was created. This is important so we
    # can filter them based on their age.
    role_create_date: datetime.datetime = role["CreateDate"]

    # Let's filter such that we only get the roles back that were created in the
    # last 90 days.
    if ninety_days_ago < role_create_date:

        # Let's extract the name of the role and save it for later. This is one
        # of the things that we are looking for.
        role_name: str = role["RoleName"]

        try:

            # Let's also request a list of all the managed policies associated
            # with this role. We were looking for this metadata as well.
            response_managed: dict = client_iam.list_attached_role_policies(
                RoleName=role_name
            )

            # Let's do the same thing fo the UNmanaged policies as well.
            response_unmanaged: dict = client_iam.list_role_policies(
                RoleName=role_name
            )

        # Catch and diffuse cases where we dont have the perms to view a policy
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "AccessDenied":
                pass
        
        # Let's get the list of the names of the managed policies. We don't have
        # to do this with the UNmanaged policies. But, with the managed ones,
        # the names are a bit nested in the response and require a little more 
        # work than just getting the list of names handed to us in the response.
        managed_policy_names: list = []
        for att_policy in response_managed["AttachedPolicies"]:
            managed_policy_names.append(att_policy["PolicyName"])

        # Now, we've obtained all the metadata that we were looking for. Let's 
        # package it up real cute in this nice dictionary and ship it off to the
        # list of role metadata that was created in the beginning of the
        # script. Then, once we have all of the roles done, we can work with
        # each dictionary easily, and print off the values.
        role_metadata.append({
            "RoleName" : role_name,
            "CreateDate" : role_create_date,
            "ManagedPolicies" : managed_policy_names,
            "UnmanagedPolicies" : response_unmanaged["PolicyNames"],
        })



# Let's make this nice function to print our policies, since there are two
# categories of them, and it is best practice not to repeat ourselves.
def print_policies(category_name: str, display_category: str, role: dict):
    """_Print the list of policies associated with a role. Works for
    both categories of policies._

    Args:
        category_name (str): _The category of policy it is. 
            `"UnmanagedPolicies"` or `"ManagedPolicies"`._
        display_category (str): _What you would like to title the section the 
            policies display under when they are printed out. For instance,
            "Managed Policies"._
        role (dict): _The role that will have it's policies printed._
    """
    # Let's consider if the role has any policies under the category or not. 
    if role[category_name]:

        # If it does, then we can print the section title.
        print(f"  {display_category}:")

        # Now, we just print out the policies in a list
        for policy_name in role[category_name]:

            # We will make an exception for policies called "Iam_Policies",
            # That means it is beyond the boundary of our permissions.
            if policy_name == "Iam_Policies":
                print("    (AccessDenied) Unauthorized to view policies")
            else:
                print(f"   - {policy_name}")




for role in role_metadata:
    print(f"\n  {role['RoleName']}, created {str(role['CreateDate'])}")
    print_policies("ManagedPolicies", "Managed Policies", role)
    print_policies("UnmanagedPolicies", "Unmanaged Policies", role)
