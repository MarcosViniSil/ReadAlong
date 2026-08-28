from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseSettings):
    s3_endpoint: str | None = None
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    s3_region: str = "us-east-1"


def load_bucket_config() -> Settings:
    return Settings(
        s3_endpoint=os.getenv("S3_ENDPOINT","http://localhost:9000",),
        s3_access_key=str(os.getenv("S3_ACCESS_KEY", "")),
        s3_secret_key=str(os.getenv("S3_SECRET_KEY", "")),
        s3_bucket=str(os.getenv("S3_BUCKET", "")),
    )

