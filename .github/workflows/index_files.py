#!/usr/bin/env python3

import boto3
import os
import urllib.parse

client = boto3.client('s3')

bucket = os.environ['S3_BUCKET']

response = client.list_objects_v2(
    Bucket=bucket,
    Prefix='aws-account-automation/'
    )

for o in response['Contents']:
	url = f"https://{bucket}.s3.amazonaws.com/{o['Key']}"
	print(f"## {o['Key']}")
	print(f"* [Quick Deploy URL](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateURL={urllib.parse.quote(url)})")
	print(f"* [HTTP URL (latest)]({url})")
	print(f"* S3 URL (latest) - s3://{bucket}/{o['Key']}")
	print("* Previous Version HTTP URLs:")
	r2 = client.list_object_versions(
		Bucket=bucket,
		Prefix=o['Key']
	)
	for v in r2['Versions']:
		print(f"\t * [{v['LastModified']} ({v['VersionId']})](https://{bucket}.s3.amazonaws.com/{o['Key']}?versionId={v['VersionId']})")

