import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

class SSMConfigProvider:
    """
    Fetches configuration secrets from AWS SSM Parameter Store.
    Falls back to environment variables if SSM is unreachable or key is missing.
    """
    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name
        self._ssm_client = None

    @property
    def ssm(self):
        if not self._ssm_client:
            try:
                self._ssm_client = boto3.client("ssm", region_name=self.region_name)
            except Exception as e:
                print(f"[SSM] Warning: Failed to initialize Boto3 client: {e}")
                return None
        return self._ssm_client

    def get_parameter(self, path: str, default: str = None, with_decryption: bool = True) -> str:
        """
        Attempts to fetch a parameter from SSM.
        If fails, returns the default value (which usually comes from .env).
        """
        if not self.ssm:
            print(f"[SSM] Client unavailable. Using fallback for {path}.")
            return default

        try:
            print(f"[SSM] Fetching {path}...")
            response = self.ssm.get_parameter(
                Name=path,
                WithDecryption=with_decryption
            )
            val = response["Parameter"]["Value"]
            print(f"[SSM] Successfully loaded {path}")
            return val
        except (ClientError, NoCredentialsError) as e:
            print(f"[SSM] Failed to fetch {path}: {e}. using fallback.")
            return default
        except Exception as e:
            print(f"[SSM] Unexpected error for {path}: {e}. using fallback.")
            return default
