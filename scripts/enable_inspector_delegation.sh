#!/bin/bash

# Script to enable Delegated Admin in a payer account for all Regions

SECURITY_ACCOUNT=$1

if [ -z $SECURITY_ACCOUNT ] ; then
	echo "Usage: $0 <security_account_id>"
	exit 1
fi

REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text`
for r in $REGIONS ; do
  echo "Enabling Inspector Delegated Admin in $r"
  aws inspector2 enable-delegated-admin-account --delegated-admin-account-id $SECURITY_ACCOUNT --region $r

done