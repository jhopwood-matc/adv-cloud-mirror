'''
Author: Joseph Hopwood
Description: write out to a csv file 'export.csv' a report of all running EC2
Instances. Report includes InstanceId, InstanceType, State, PublicIpAddress,
Monitoring, and Name.
'''

import boto3, csv




def get_instances(name: str, value: str) -> list:
    """_Queries AWS for a filtered list of all EC2 instances._

    Args:
        name (str): _This is the name of the instance property that the
            instances will be filtered by._
        value (str): _This is the state or value of the instance property
            identified in `name` that will filter the instance data returned
            by AWS to only show instance data for instances that match._

    Returns:
        list: _Response from AWS containing all metadata of all matching ec2 
            instances on the account._
    """
    
    assert isinstance(name, str), 'name should be a str!'
    assert isinstance(value, str), 'value should be a str!'

    # Let's create a client to interface with the EC2 service.
    client = boto3.client('ec2')

    # we want to call EC2.client.describe_instances(), but there is going to
    # be too much data; we are going to invoke that through a paginator to 
    # get it in chunks.
    paginator = client.get_paginator('describe_instances')

    # Let's construct the filter for our response from AWS.
    pag_filter: list = [
        {
            'Name' : name,
            'Values' : [
                value,
            ]
        },
    ]

    # Now we can filter the data that we have to only show matching instances.
    page_list = paginator.paginate(
        Filters = pag_filter
    )

    instance_data: list = []

    # We can take all the pages of filtered instance data and add them to our
    # output. We also only want to reservation data --not group data.
    for page in page_list:
        for reservation in page['Reservations']:
            instance_data.append(reservation)

    return instance_data




def csv_writer(header: list, content: list):
    """_Write data to an export.csv in the working directory in a
    table-esque fashion._

    Args:
        header (list): _Collection of titles of the different columns._
        content (list): _Collection of Python dictionaries that contain
            data to be written with Keys that correspond to title of the column
            they are to be written in._
    """
    
    # Open a new or existing csv file in the working directory to write to.
    file = open('export.csv', 'w')

    # Let's create a DictWriter which will organize the content coming in into 
    # the correct placements under the header's titles to make it table-esque.
    writer = csv.DictWriter(file, fieldnames=header)

    # Write the titles in the first row.
    writer.writeheader()

    # Fill in the content.
    for line in content:
        writer.writerow(line)

    # Make sure to close your files!
    file.close()




def get_name(instance_metadata: dict) -> str:
    """_Retrieves the name of an instance from it's metadata._

    Args:
        instance_metadata (dict): _Metadata about the instance to be queried for
            it's name. This is typically returned from a
            `EC2.client.describe_instances()` call._

    Returns:
        str: _Name of the instance. Will return 'N/A' if there is none._
    """
    # Check to see if the instance even has any tags to being with. If it
    # does not, then we can just return N/A and be done.
    if not 'Tags' in instance_metadata:
        return 'N/A'
    
    # Well, it has tags. Now, we have to see if it has a Name tag. 
    else:
        tags: list = instance_metadata['Tags']
        has_name_tag: bool = False
        index_of_name_tag: int
        
        # Let's check all the tags to see if one is a Name tag. If there is one,
        # We will save the index of it and come back for the value.
        for i in range(len(tags)):
            if tags[i]['Key'] == 'Name':
                has_name_tag = True
                index_of_name_tag = i
                break

        # Given that it has a Name tag, let's return the value
        if has_name_tag:
            return tags[index_of_name_tag].get('Value', 'N/A')
        
        # Given that it did not have a Name tag. Let's return N/A
        else:
            return 'N/A'
        



def main():

    # Let's get a list of all the metadata of only running instances
    response: list = get_instances('instance-state-name', 'running')

    # Let's define the titles of the columns in the csv
    header: list = [
        'InstanceId',
        'InstanceType',
        'State',
        'PublicIpAddress',
        'Monitoring',
        'Name',
    ]

    content: list = []
    
    # Let's fill our content up with the relevant data that we want.
    for reservation in response:
        for instance in reservation['Instances']:
            content.append(
                {
                    'InstanceId' : instance['InstanceId'],
                    'InstanceType' : instance['InstanceType'],
                    'State' : instance['State']['Name'],
                    'PublicIpAddress' : instance.get('PublicIpAddress', 'N/A'),
                    'Monitoring' : instance['Monitoring']['State'],
                    'Name' : get_name(instance)
                }
            )

    # Let's write out or data to a csv file nice and neat.
    csv_writer(header, content)




if __name__ == "__main__":
    main()