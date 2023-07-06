#!/bin/bash

ROLENAME=$1

if [ -z $ROLENAME ] ; then
  echo "usage $0 <ROLENAME>"
  exit 1
fi

while read line ; do

  # extract the values we need
  ACCOUNT_ID=`echo $line | awk '{print $1}'`

  aws sts assume-role --role-arn arn:aws:iam::$ACCOUNT_ID:role/$ROLENAME --role-session-name Disable-Security-Hub-Standards --query Credentials > ${ACCOUNT_ID}_creds.json

  export AWS_SECRET_ACCESS_KEY=`cat ${ACCOUNT_ID}_creds.json | jq .SecretAccessKey -r`
  export AWS_ACCESS_KEY_ID=`cat ${ACCOUNT_ID}_creds.json | jq .AccessKeyId -r `
  export AWS_SESSION_TOKEN=`cat ${ACCOUNT_ID}_creds.json | jq .SessionToken -r `
  rm ${ACCOUNT_ID}_creds.json

  REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text`
  for r in $REGIONS ; do
    echo "Disabling all Security Hub standards in $ACCOUNT_ID ${r}"
    STANDARDS=`aws securityhub get-enabled-standards --query StandardsSubscriptions[].StandardsSubscriptionArn --output text --region $r`
    if [[ ! -z "$STANDARDS" ]] ; then
      aws securityhub batch-disable-standards --standards-subscription-arns $STANDARDS --region $r --output text
    else
      echo "No enabled standards in $ACCOUNT_ID ${r}"
    fi
  done
  unset AWS_SECRET_ACCESS_KEY AWS_ACCESS_KEY_ID AWS_SESSION_TOKEN

done < <(aws organizations list-accounts --query Accounts[].[Id,Status] --output text | grep ACTIVE )

