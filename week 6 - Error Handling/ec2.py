'''
Author: Joseph Hopwood
Description: Deploys an EC2 Instance (t2.micro, latest AL2 AMI) into the default
VPC. Outputs the instance ARN, IP, and tags. Then, adds tags, outputs the new
tags. Then, the instance is terminated and it's state is reported. Now, with 
Error Handling.
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




def main():

    # This is the control of the AWS "dry run" option.
    dryrun: bool = False

    # First, let's create a client to interact with the EC2 service.
    client = boto3.client('ec2')

    try:
        # Let's retrieve the latest Amzon Linux 2 AMI version's ID.
        ami_id: str = get_image(client)

        # Let's create a t2.micro EC2 instance using that AMI.
        instance_id: str = create_ec2(client, ami_id, dryrun)

        # We are interested in interacting with the instance we just created more
        # directly. Boto3 supports 'resources', which are higher-level
        # representations of AWS interfaces as Python Objects.

        # Using this interface, we can, then, interact with ec2 instance as a
        # Python Object

        # Let's create that resource
        ec2_resource = boto3.resource('ec2')

        # Now, we can create a Python Object that represents the AWS EC2 Instance
        # and let's us interface with it directly. 
        ec2_instance = ec2_resource.Instance(instance_id)

        # What is the ID of our EC2 instance? Let's have it tell us.
        print(ec2_instance.instance_id)

        # Let's wait for it to finish spinning up before we interact with it.
        ec2_instance.wait_until_running()

        # Let's have it tell us what the public IP address of it is.
        print(ec2_instance.public_ip_address)

        # Let's have it also tell us what tags it has. It should have none.
        print_tags(ec2_instance)

        # Let's add a name tag to the instance.
        name_tag: dict[str] = {
            'Key' : 'Name',
            'Value' : 'Joseph',
        }
        _ = ec2_instance.create_tags(
            DryRun = dryrun,
            Tags = [name_tag]
        )

        # Let's see if the tag was added.
        print_tags(ec2_instance)

        # Okay, now we can terminate it as per the instructions.
        ec2_instance.terminate()

        # Let's wait for it to terminate, then let's check it's state. 
        ec2_instance.wait_until_terminated()

        # Tell us what state it is in!
        print(f"instance is {ec2_instance.state['Name']}.")

    except botocore.exceptions.ClientError as error:

        # Catch if the region is misconfigured
        if error.response["Error"]["Code"] == "UnauthorizedOperation":
            print("You are not authorized to do this! Check your region in " \
                "~/.aws/config")
            print(f"Currently in -> {client.meta.region_name}")
            
        else:
            print(error)




if __name__ == "__main__":
    main()