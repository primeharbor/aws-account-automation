#!/bin/bash

# Script to enable Inspector in each region in the Delegated Admin Account

# We need to get a list of the accounts to then add as members. This actually comes from the Organizations API which we now have access to as a Delegated Admin Child
ACCOUNT_LIST=`aws organizations list-accounts --query Accounts[].Id --output text`
ME=`aws sts get-caller-identity --query Account --output text`

trap "exit 1" SIGINT

REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text`
for r in $REGIONS ; do
  echo "Associating accounts in $r"

  for a in $ACCOUNT_LIST ; do
    if [ $a != $ME ] ; then
      aws inspector2 associate-member --account-id $a --region $r --output text
    fi
  done

  echo "Enable Inspector in this delegated Admin account"
  aws inspector2 enable --resource-types EC2 --account-ids $ACCOUNT_LIST --output text --region $r --no-paginate
  sleep 10

  echo "Update the org config to auto-enable new accounts"
  aws inspector2 update-organization-configuration --auto-enable ec2=true,ecr=false,lambda=false --region $r

done
