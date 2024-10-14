'''
Author: Joseph Hopwood
Description: This is a script that will print out the first 100 buckets on 
the user's AWS account along with their contents.
Example Format:

Bucket Name: example-bucket {
Object(s):
 - error.html,
 - index.html,
},
...

'''

import boto3

# Let's start off by getting a low level client so that we can interact with
# the s3 service.
client = boto3.client('s3')

# Let's request a list of information on the first 100 buckets in our account.
list_buckets_response = client.list_buckets(
    MaxBuckets = 100,
)

# Now that we have the information for each bucket, we can print out what we
# want from them. We want just the name and the contents
for bucket in list_buckets_response['Buckets']:

    # First, let's get that name.
    bucket_name = bucket['Name']

    # Now, we can print it out.
    print('Bucket Name: ' + bucket_name + ' {\nObject(s):')

    # We can use the bucket name, then, to obtain a list of the objects within 
    # it with this API call.
    list_objects_response = client.list_objects_v2(
        Bucket = bucket_name
    )

    # From that previous response, let's print the names of each object
    for object in list_objects_response['Contents']:
        object_name = object['Key']
        print(' - ' + object_name + ',')

    print('},')
    
