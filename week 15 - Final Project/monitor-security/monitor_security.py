'''
Author: Joseph Hopwood
Description: lists all EC2 instances and gets the security groups of each.
Checks each security group to ensure that port 22 is not open to the internet 
(eg: 0.0.0.0/0). If the security group (sg) is open to a specific IP address, 
that is ok. If port 22 is open to the internet, removes access to port 22.
'''

import boto3
import botocore
import botocore.exceptions





class SecurityGroup:
    """
    Client cache of only key AWS Security Group Metadata values and inbound rule
    metadata needed for program functionality.
    """


    class InboundRule:
        """
        Client cache of only key AWS Inbound Rule Metadata values for a rule
        associated with a security group.
        """


        def __init__(self, id: str, from_port: int, to_port: int, cidr_ipv4: str):
            """Initialize a new Inbound Rule.

            Args:
                id (str): Amazon SecurityGroupRuleId of inbound rule.
                from_port (int): First port in the port range.
                to_port (int): Final port in the port range.
                cidr_ipv4 (str): Ipv4 Cidr range.
            """
            self.id: str = id
            self.from_port: int = from_port
            self.to_port: int = to_port
            self.cidr_ipv4: str = cidr_ipv4          




    def __init__(self, id: str, name: str):
        """Initialize a new SecurityGroup. While initializing, the sg will make
        an API call to AWS and populate its inbound rules.

        Args:
            id (str): The ID of the Security Group or "GroupId".
            name (str): The name of the Security Group of "GroupName".
        """
        self.id: str = id
        self.name: str = name

        # This will cache key metadata for each inbound rule associated with
        # this Security Group.
        self.rules: list[self.InboundRule] = []

        # Reaching out to AWS to get a list of ALL sg rules associated with sg.
        client = boto3.client("ec2")
        response: dict = client.describe_security_group_rules(
            Filters=[
                {
                    "Name": "group-id",
                    "Values": [self.id]
                }
            ]
        )

        # Filter out all rules that aren't inbound IPv4 rules. Than cache all
        # associated inbound ipv4 rules.
        for rule in response["SecurityGroupRules"]:
            if not rule["IsEgress"]:
                try:
                    self.rules.append(
                        self.InboundRule(
                            id=rule["SecurityGroupRuleId"],
                            from_port=rule["FromPort"],
                            to_port=rule["ToPort"],
                            cidr_ipv4=rule["CidrIpv4"]
                        )
                    )
                # for ipv6 rules
                except KeyError:
                    pass



    
    def print(self):
        """
        Display formatted security group details, including: id, name, a
        security summary, port 22 statuses, and sg inbound rules with their
        respective ids and properties.
        """

        port_22: int = 22
        public_ipv4 = "0.0.0.0/0"

        print(f"Name: {self.name}")
        print(f"ID: {self.id}")

        # If the sg has associated rules, then we can go the first route of
        # parsing through them and identifying vulnerabilities and telling the
        # user this detailed information as well as listing each rules's config.
        if self.rules:

            print("Security Summary: ")

            # We look through all the rules and set these *SG LEVEL* switches
            # accordingly. We only count it as public if port 22 is open first. 
            # Of course, they are defaulted to False.
            is_open_22: bool = False
            is_public: bool = False

            for rule in self.rules:
                
                # Temporary *RULE LEVEL* switches to evaluate the config of 
                # each rule.
                _is_open_22: bool = (rule.from_port <= port_22 <= rule.to_port)
                _is_public: bool = rule.cidr_ipv4 == public_ipv4

                # Based on what we find for how the rule is configured, we
                # update the sg level switches accordingly.
                if _is_open_22 and _is_public:
                    is_open_22 = True
                    is_public= True
                elif _is_open_22 and not _is_public:
                    is_open_22 = True

            # Then, we can also print our what we found.
            if is_open_22 and is_public:
                print(" - Status: INSECURE")
                print("    + Port 22: OPEN")
                print("    + Access: PUBLIC")

            elif is_open_22 and not is_public:
                print(" - Status: Secure")
                print("    + Port 22: OPEN")
                print("    + Access: private")

            else:
                print(" - Status: Secure")
                print("    + Port 22: closed")

            print("Rules:")

            # Printing out configurations of each rule associated with the sg.
            for rule in self.rules:
                print(f" - rule_id: {rule.id}")
                print(f"    + cidr_ipv4: {rule.cidr_ipv4}")
                print(f"    + from_port: {rule.from_port}")
                print(f"    + to_port: {rule.to_port}")
            print(" ")

        # Otherwise, there were not rules associated with the sg. In which case,
        # There is no reason to evaluate things that dont exist, and we can
        # assume that the sg is secure.
        else:
            print(" - Status: Secure\n")
    



    def remove_unsafe_rules(self):
        """
        Call to AWS to delete unsafe rules (publicly open port 22 access)
        from a sg. Updates the local cache as well.
        """

        port: int = 22
        public_ipv4 = "0.0.0.0/0"

        for rule in self.rules:

            is_open_22: bool = (rule.from_port <= port <= rule.to_port)
            is_public: bool = rule.cidr_ipv4 == public_ipv4

            if is_open_22 and is_public:

                # Notify user.
                print("REMOVING UNSAFE RULE(S):" )
                print(f"Group: {self.name} / {self.id}")
                print(f" - {rule.id}")
                print(" ")

                # Removal API call.
                client = boto3.client("ec2")
                response: dict = client.revoke_security_group_ingress(
                    SecurityGroupRuleIds=[rule.id],
                    GroupId=self.id
                )

                # Local cache removal.
                self.rules.remove(rule)

                # Redisplay sg details to show the user the change.
                print("SUCCESSFULLY REMOVED | NEW CONFIGURATION")
                self.print()
                


    

def main():

    # Let's get our low level client to make API calls.
    client_ec2 = boto3.client('ec2')

    # First lets retrieve all of the ec2 instances on the account.
    resp_all_instances: dict = {}
    try:
        resp_all_instances = client_ec2.describe_instances()

    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "RequestExpired":
            print("~/.aws tokens likely expired. Please change.")
            exit()

    # A list of all security groups currently in use across all EC2 instances.
    security_groups: list[SecurityGroup] = []

    # Storing the unique ids of active ec2 sgs temporarily so we dont get
    # duplicate sgs in the local cache.
    unique_ids: list[str] = []

    print("\nRETRIEVING ACTIVE EC2 SECURITY GROUPS...\n")

    # OK, let's populate our active security groups
    for reservation in resp_all_instances["Reservations"]:

        for instance in reservation["Instances"]:

            for sg in instance["SecurityGroups"]:

                if sg["GroupId"] not in unique_ids:

                    unique_ids.append(sg["GroupId"])

                    security_groups.append(
                        SecurityGroup(
                            id=sg["GroupId"],
                            name=sg["GroupName"]
                        )
                    )
    del unique_ids
    
    print("IDENTIFIED THE FOLLOWING ACTIVE EC2 SECURITY GROUPS:\n")

    # Use this to count the sgs when printing.
    i: int = 1

    # Print the detailed information of all the sgs
    for sg in security_groups:
        print(f"{'_' * 10} Group {i} {'_' * 10}")
        sg.print()
        i+=1

    for sg in security_groups:
        sg.remove_unsafe_rules()




if __name__ == "__main__":
    main()