import boto3
from botocore.client import Config

s3 = boto3.client(
    "s3",
    endpoint_url="http://192.168.19.11:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="password",
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)


bucket = "meu-bucket"
key = "output.wav"

s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=b"Hello World!"
)