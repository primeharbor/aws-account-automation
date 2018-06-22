#!/bin/bash
set -e

# Need to upload TEMPLATES to S3 before validating due to template-body MAX 51K length
# https://docs.aws.amazon.com/cli/latest/reference/cloudformation/validate-template.html#options
REPO_NAME="${PWD##*/}"
S3_BUCKET=$AdminCentralInfraCfBucket
S3_BUCKET_PATH="$REPO_NAME/$TRAVIS_BRANCH"
S3_BUCKET_URL="s3://$S3_BUCKET/$S3_BUCKET_PATH"

# Upload local templates
TEMPLATES=cloudformation/*
for template in $TEMPLATES
do
  dir="${template%/*}"
  file="${template##*/}"
  extension="${file##*.}"
  filename="${file%.*}"
  aws s3 cp ${template} $S3_BUCKET_URL/${file}
done
