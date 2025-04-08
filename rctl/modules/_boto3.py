import string

import boto3
from botocore.exceptions import ClientError

from ..base import Operator


class Boto3Controller(Operator):
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def get_instance(self):
        return boto3.client(**self._kwargs)

    def get_service_name(self):
        return self._kwargs["service_name"]

    @staticmethod
    def get_operator(type: str):
        if type == "policy":
            return PolicyController
        else:
            raise TypeError()


class PolicyController(Boto3Controller):
    def create(
        self, bucket_name: str, policy_name: str, custom_policy: str = None, **params
    ):
        if policy_name and custom_policy:
            raise ValueError()

        _policy = (
            policies[self.get_service_name()][policy_name]
            if policy_name
            else custom_policy
        )
        policy_string = build_template(_policy, bucket_name=bucket_name)

        client = self.get_instance()
        assert (
            self.get_service_name() == "s3"
        )  # boto3 からサービス名が取れるのでservice_name 引数はコネクション側に
        res: dict = client.put_bucket_policy(Bucket=bucket_name, Policy=policy_string)
        return True, res

    def delete(
        self, bucket_name: str, policy_name: str, custom_policy: str = None, **params
    ):
        client = self.get_instance()
        res: dict = client.delete_bucket_policy(Bucket=bucket_name)
        return True, res

    def exists(
        self, bucket_name: str, policy_name: str, custom_policy: str = None, **params
    ):
        client = self.get_instance()
        try:
            res: dict = client.get_bucket_policy(Bucket=bucket_name)
        except ClientError as e:
            ok, err_code = safe_get(e.response, "Error", "Code")
            if not ok:
                raise
            return False, err_code
        return True, res["Policy"]

    def absent(
        self, bucket_name: str, policy_name: str, custom_policy: str = None, **params
    ):
        ok, msg = self.exists(bucket_name=bucket_name)
        if ok:
            return False, "Exists bucket policy"
        else:
            return True, None


def safe_get(obj: dict, *keys):
    undefined = object()
    if len(keys) == 0:
        raise ValueError()

    for k in keys:
        result = obj.get(k, undefined)
        if result is undefined:
            return False, f"Key not founc{k}"

    return True, result


def build_template(_txt: str, **kwargs):
    return string.Template(_txt).substitute(**kwargs)


policies = {
    "s3": {
        "public": """{
    "Version": "2012-10-17",
    "Statement": [
        {
        "Effect": "Allow",
        "Principal": {
            "AWS": [
            "*"
            ]
        },
        "Action": [
            "s3:GetBucketLocation",
            "s3:ListBucket",
            "s3:ListBucketMultipartUploads"
        ],
        "Resource": [
            "arn:aws:s3:::${bucket_name}"
        ]
        },
        {
        "Effect": "Allow",
        "Principal": {
            "AWS": [
            "*"
            ]
        },
        "Action": [
            "s3:PutObject",
            "s3:AbortMultipartUpload",
            "s3:DeleteObject",
            "s3:GetObject",
            "s3:ListMultipartUploadParts"
        ],
        "Resource": [
            "arn:aws:s3:::${bucket_name}/*"
        ]
        }
    ]
    }""",
        "private": """{"Version": "2012-10-17", "Statement": []}""",
    }
}
