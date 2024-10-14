'''
Author: Joseph Hopwood
Description: Module containing EC2 functions
'''

import boto3, botocore, botocore.exceptions




def get_image(ec2_client) -> str:
    """_Queries AWS for the latest Amazon Linux 2 AMI and returns the ID of it._

    Args:
        ec2_client: _An established client interface with AWS
            EC2 Service._

    Returns:
        str: _The ID of the latest version of the Amzon Linux 2 AMI._
    """
    # Let's make a filter that defines our search terms.
    latest_ami_filter: list[dict[str]] = [
        {
            'Name' : 'description',
            'Values' : ['Amazon Linux 2 AMI*']
        },
        {
            'Name' : 'architecture',
            'Values' : ['x86_64']
        },
        {
            'Name' : 'owner-alias',
            'Values' : ['amazon']
        }
    ]   

    # Now, we can query what images match our filter we just made.
    describe_instances_response: dict[str] = ec2_client.describe_images(
        Filters = latest_ami_filter,
    )

    # This should use a paginator! But, that's out of the scope of this
    # assignment

    # We get a lot of results in our response from the query. We only
    # want the ID of the first, most relevant, result. We extract that
    # here.
    latest_ami_id: str = describe_instances_response['Images'][0]['ImageId']

    # Viola!
    return latest_ami_id




def create_ec2(
        ec2_client,
        ami_id: str,
        dryrun: bool = True
) -> str:
    """_Create a t2.micro EC2 instance. Hardcoded SG,SSH,userdata values._

    Args:
        ec2_client: _An established client interface with AWS EC2 Service._
        ami_id (str): _The ID of the AMI that the instance will run._
        dryrun (bool, optional): _Dry run switch for testing. Defaults to True._

    Returns:
        str: _The ID of the EC2 Instance that was created._
    """

    # Let's create a (single) t2.micro instance and store the response.
    response: dict = ec2_client.run_instances(
        ImageId = ami_id,
        InstanceType = 't2.micro',
        MaxCount = 1,
        MinCount = 1,
        DryRun = dryrun,
        SecurityGroups=['WebSG'],
        KeyName='vockey',
        UserData='''
            #!/bin/bash -ex
            # Updated to use Amazon Linux 2
            yum -y update
            yum -y install httpd php mysql php-mysql wget unzip
            /usr/bin/systemctl enable httpd
            /usr/bin/systemctl start httpd
            cd /var/www/html
            wget https://aws-tc-largeobjects.s3-us-west-2.amazonaws.com/CUR-TF-100-ACCLFO-2/lab6-scaling/lab-app.zip
            unzip lab-app.zip -d /var/www/html/
            chown apache:root /var/www/html/rds.conf.php''',
    )

    # Okay, hopefully it was created successfully, now we are going to extract
    # the ID of it from the response. 
    instance_id: str = response['Instances'][0]['InstanceId']

    return instance_id




def print_tags(ec2_instance):
    """_Print a formatted list of the tags associated with an EC2 Instance._

    Args:
        ec2_instance: _The Pythonic representation of the 
            EC2 instance that is going to have it's tags queried._
    """

    # Let's retieve they unformatted tags that the instance has.
    tags: dict = ec2_instance.tags

    # if there aren't any tags anyhow, let's not proceed any further.
    if not tags:
        print('There are no tags associated with this instance!')

    # Let's get a nice formatted block of the tags. 
    else:
        print('Tags {')
        for tag in tags:
            print(f"  {tag['Key']} : {tag['Value']}")
        print('}')