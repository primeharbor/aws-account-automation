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

  DETECTOR=`aws guardduty list-detectors --query DetectorIds[] --output text --region $r `
  if [ -z $DETECTOR ] ; then
    echo "Creating a Detector in the Organizations Management account in $r"
    DETECTOR=`aws guardduty create-detector  --output text --region $r --finding-publishing-frequency ONE_HOUR --enable`
    if [ -z $DETECTOR ] ; then
      echo "Failed to create a detector in $r. Aborting script"
      exit 1
    fi
  fi

done