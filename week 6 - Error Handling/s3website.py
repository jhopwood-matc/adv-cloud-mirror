#!/usr/bin/env python3
'''
Author: Joseph Hopwood
Description: Script to create an S3 Bucket in AWS to be used as a website.
'''

import boto3, json, argparse, string, random
import botocore, botocore.exceptions

# Let's create a parser to handle the arguments passed ot the script.
# Let's also add some helpful about metadata.
parser: argparse.ArgumentParser = argparse.ArgumentParser(
    prog="S3 Bucket Generation Script",
    description="Create an AWS S3 bucket with a unique name",
)

# Let's add the parameter to give the bucket a name when calling the script.
parser.add_argument(
    "-s", "--sitename",
    type=str,
    help="Unique name of the s3 bucket in AWS",
    )

# ...registering the arguments passed ...
args = parser.parse_args()

# Let's start off by getting a low level client for s3
s3_client = boto3.client('s3')

# Here's the name of our bucket. It will either be what the script user passed
# in when the script was called, or it will be a random 10 char string.
bucket_name: str = ""
if args.sitename:
    bucket_name = args.sitename
else:
    bucket_name = "".join(random.choices(string.ascii_lowercase, k=10))

try:
    # Let's make our bucket using that name.
    s3_client.create_bucket(
        Bucket = bucket_name
    )

    # Let's enable public access on our bucket.
    s3_client.delete_public_access_block(
        Bucket = bucket_name
    )

    # Now, Let's define a policy for our bucket.
    bucket_policy = {
        'Version' : '2012-10-17',
        'Statement' : [
            {
                'Sid' : 'AddPerm',
                'Effect' : 'Allow',
                'Principal' : '*',
                'Action' : ['s3:GetObject'],
                'Resource' : "arn:aws:s3:::%s/*" % bucket_name,
            },
        ]
    }

    # Let's convert the policy to a string in json format, because the boto3
    # functions only accept that format.
    bucket_policy_json = json.dumps(bucket_policy)

    # Let's apply that previously defined policy to our bucket.
    put_bucket_policy_response = s3_client.put_bucket_policy(
        Bucket = bucket_name,
        Policy = bucket_policy_json
    )

    # We are going to use this bucket to server static content, so let's define
    # a configuration of it. And, let's put it here for easier readability
    # and maintenance. 
    website_configuration = {
        'ErrorDocument' : {
            'Key' : 'error.html'
        },
        'IndexDocument' : {
            'Suffix' : 'index.html'
        },
    }

    # Okay, now let's go ahead and apply that configuration.
    put_bucket_website_response = s3_client.put_bucket_website(
        Bucket = bucket_name,
        WebsiteConfiguration = website_configuration
    )

    # Okay so, in our configuration we defined two documents for the website,
    # and 'index.html' and an 'error.html' (see above). Those don't actually
    # exist in the bucket yet, so the website will be confused. We're gonna
    # go ahead and upload them so things work properly. Both documents are
    # going to be uploaded using originals that exist here in the working
    # directory.

    # First, we open the file to store it as an object. We use 'rb' because
    # it needs to be uploaded as bytes.
    error_file = open('./error.html', 'rb')

    # Then, we can call put_object() to throw the document into the bucket.
    put_object_response_error = s3_client.put_object(
        Body = error_file,
        Bucket = bucket_name,
        # we name it here; let's use the correct (same) name.
        Key = 'error.html', 
        ContentType = 'text/html'
    )
    # Let's close our file when we are done with it.
    error_file.close()

    # Then we repeat the above process a second time for the index document.
    index_file = open('./index.html', 'rb')
    put_object_response_error = s3_client.put_object(
        Body = index_file,
        Bucket = bucket_name,
        Key = 'index.html',
        ContentType = 'text/html'
    )
    index_file.close()


except botocore.exceptions.ClientError as error:

    # Catch invalid credentials
    if error.response["Error"]["Code"] == "InvalidToken":
        print("Invalid Token: Please update your ~/.aws/credentials file!")

    # Catch the bucket name is not unique
    elif error.response["Error"]["Code"] == "BucketAlreadyExists":
        print(
            "Bucket {} already exists!".format(
                error.response['Error']['BucketName']
            )
        )

    else:
        print(error)