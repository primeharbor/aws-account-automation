#!/bin/bash

# Script to enable Delegated Admin in a payer account for all Regions

SECURITY_ACCOUNT=$1

if [ -z $SECURITY_ACCOUNT ] ; then
	echo "Usage: $0 <security_account_id>"
	exit 1
fi

REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text`
for r in $REGIONS ; do
  echo "Enabling SecurityHub Delegated Admin in $r"
  aws securityhub enable-organization-admin-account --admin-account-id $SECURITY_ACCOUNT --region $r
  aws securityhub enable-security-hub --no-enable-default-standards --output text --region $r 

done