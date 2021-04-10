#!/bin/bash

#
# Deploy the CloudWatch Events -> Lambda pipeline that pushes the GuardDuty finding to Slack
# This must be done in all regions

CHANNEL=$1
WEBHOOKSECRET=$2

if [ -z $WEBHOOKSECRET ] ; then
	echo "usage $0 <channel_name> <WEBHOOKSECRET>"
	exit 1
fi

ACCOUNT_NAME=`aws iam list-account-aliases --query AccountAliases --output text`


REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text`

for r in $REGIONS ; do
	echo "Deploying Slack Stack in $r"
	aws cloudformation create-stack --region $r --output text \
	    --stack-name GuardDutyToSlack-${r} \
	    --template-url https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/GuardDuty-to-Slack-Template.yaml \
	    --capabilities CAPABILITY_NAMED_IAM --parameters \
	    ParameterKey=pSlackChannel,ParameterValue="#${CHANNEL}" \
	    ParameterKey=pAccountDescription,ParameterValue="$ACCOUNT_NAME" \
	    ParameterKey=pSlackWebhookSecretRegion,ParameterValue="us-east-1" \
	    ParameterKey=pSlackWebhookSecret,ParameterValue="$WEBHOOKSECRET"
	if [ $? -eq 0 ] ; then
	    echo "Waiting for stack completion"
	    aws cloudformation wait stack-create-complete --stack-name GuardDutyToSlack-${r} --region $r
	fi
done