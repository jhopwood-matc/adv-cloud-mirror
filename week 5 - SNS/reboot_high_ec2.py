'''
Author: Joseph Hopwood
Description: Deploys an EC2 instance running a small web application. Creates
a new SNS topic, and subscribes inputted email to it. If the EC2 instance
reaches high CPU usage, it will reboot the instance, and send an alert email.
'''

import boto3, ec2, sns




def main():

    # Script is a wet run: we are not testing.
    dryrun: bool = False

    # Let's get our account ID; we need this for cloudwatch to perform actions
    # on our instance when the alarm triggers.
    sts_client = boto3.client('sts')
    account_id: str = sts_client.get_caller_identity()['Account']

    # Let's get a ec2 client going so we can make and EC2 instance
    ec2_client = boto3.client('ec2')

    # Let's get the latest AL2 AMI ID
    ami_id: str = ec2.get_image(ec2_client)

    # Let's make our EC2 Instance using that ami
    instance_id: str = ec2.create_ec2(ec2_client, ami_id, dryrun)

    # We are going to create a topic, and then subscribe ourselves to it. Let's
    # Define the name here.
    topic_name: str = "ExampleTopic"

    # Here we create a our topic. It's an endpoint that will handle information
    # passed to it, and then push it out to subscribers.
    topic_arn: str = sns.create_sns_topic(topic_name)

    # Let's get the email from the user that they want to subscribe to the topic
    email = input("Enter email: ")

    # Let's subscribe ourselves to it. 
    sub_arn: str = sns.subscribe_email(topic_arn, email)

    # Finally, let's create the alarm that is going to reboot our instance when
    # the average CPU Util is >= 70% for two data points within 10 minutes. it
    # will also send us an email at that time because it is going to pass this
    # information to the topic that we created.
    cloudwatch_client = boto3.client('cloudwatch')
    _ = cloudwatch_client.put_metric_alarm(
        AlarmName='Web_server_HIGH_CPU_Utilization',
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        EvaluationPeriods=2,
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Period=300,
        Statistic='Average',
        Threshold=70.0,
        ActionsEnabled=True,
        AlarmActions=[
            f"arn:aws:swf:us-east-1:{account_id}:action/actions/AWS_EC2.Insta" \
            f"nceId.Reboot/1.0",
            f"arn:aws:sns:us-east-1:{account_id}:{topic_name}",
        ],
        AlarmDescription='Alarm when server CPU is greater than 70%',
        Dimensions=[
            {
                'Name' : 'InstanceId',
                'Value' : instance_id
            },
        ]
    )




if __name__ == "__main__":
    main()