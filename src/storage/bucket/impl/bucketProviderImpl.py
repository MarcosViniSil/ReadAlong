from storage.bucket.bucketProvider import BucketProvider
import boto3
from botocore.client import Config

class BucketProviderImpl(BucketProvider):

    def __init__(
        self,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
    ):
        self.bucket = bucket

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )


    async def upload(self, key, data):
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data
        )

    async def download(self, key):
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=key
        )

        return response["Body"].read()

    async def delete(self, key):
        self.client.delete_object(
            Bucket=self.bucket,
            Key=key
        )

    async def exists(self, key):
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=key
            )
            return True
        except self.client.exceptions.ClientError:
            return False