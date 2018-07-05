import boto3

ACC_KEY = 'xxxx'
SEC_KEY = 'xxxx'
REGION = 'xxxx'
EP = 'https://xxxx.xxx'


client = boto3.client(
    'ec2',
    aws_access_key_id=ACC_KEY,
    aws_secret_access_key=SEC_KEY,
    region_name=REGION,
    endpoint_url=EP
)

ec2 = boto3.resource(
    'ec2',
    aws_access_key_id=ACC_KEY,
    aws_secret_access_key=SEC_KEY,
    region_name=REGION,
    endpoint_url=EP
)
