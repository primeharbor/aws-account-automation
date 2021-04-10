#!/bin/bash

# Script to enable Delegated Admin in a payer account for all GuardDuty Regions

GD_ACCOUNT=$1

if [ -z $GD_ACCOUNT ] ; then
	echo "Usage: $0 <account_id_of_account_to_run_guardduty>"
	exit 1
fi

REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text`
for r in $REGIONS ; do
  echo "Enabling GuardDuty Delegated Admin in $r"
  aws guardduty enable-organization-admin-account --admin-account-id $GD_ACCOUNT --region $r
done