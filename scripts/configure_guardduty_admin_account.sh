#!/bin/bash

# Script to enable GuardDuty in each region in the Delegated Admin Account

# We need to get a list of the accounts to then add as members. This actually comes from the Organizations API which we now have access to as a Delegated Admin Child
aws organizations list-accounts | jq '[ .Accounts[] | { AccountId: .Id, Email: .Email } ]' > ACCOUNT_INFO.txt

REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text`
for r in $REGIONS ; do
  echo "Enabling GuardDuty Delegated Admin in $r"
  DETECTOR=`aws guardduty list-detectors --query DetectorIds[] --output text --region $r `
  if [ -z $DETECTOR ] ; then
    echo "No detector in $r, creating one"
    DETECTOR=`aws guardduty create-detector  --output text --region $r --finding-publishing-frequency FIFTEEN_MINUTES --enable`
    if [ -z $DETECTOR ] ; then
      echo "Failed to create a detector in $r. Aborting script"
      exit 1
    fi
  fi

  echo "Detector $DETECTOR in $r"
  aws guardduty update-organization-configuration --detector-id $DETECTOR --auto-enable --region $r
  aws guardduty create-members --detector-id $DETECTOR --account-details file://ACCOUNT_INFO.txt --region $r

  # Adding this line because the Original create-detector command doesn't seem to set it
  aws guardduty update-detector --detector-id $DETECTOR --finding-publishing-frequency FIFTEEN_MINUTES --region $r

  BUCKET=$1
  KMS_KEY=$2
  if [[ ! -z "$KMS_KEY" ]] ; then
    aws guardduty create-publishing-destination --detector-id $DETECTOR --destination-type S3 --destination-properties DestinationArn=$BUCKET,KmsKeyArn=$KMS_KEY --region $r
  fi

done

# cleanup
rm ACCOUNT_INFO.txt