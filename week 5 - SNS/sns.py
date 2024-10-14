

import boto3

def create_sns_topic(topic_name: str) -> str:
    """_Create a new topic. Honestly a wrapper function._

    Args:
        topic_name (str): _Desired name of new topic._

    Returns:
        str: _ARN or created topic._
    """
    
    sns_client = boto3.client('sns')

    response: dict = sns_client.create_topic(
        Name=topic_name
    )

    return response['TopicArn']




def subscribe_email(topic_arn: str, email: str) -> str:
    """_Subscribe an email to a topic._

    Args:
        topic_arn (str): _ARN of topic._
        email (str): _Email to be subscribed to topic._

    Returns:
        str: _ARN of subscription._
    """

    sns_client = boto3.client('sns')

    # Remeber to like, comment, and subscribe!
    response: dict = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=email
    )

    return response['SubscriptionArn']