#!/bin/bash

# Script to enable SecurityHub in each region in the Delegated Admin Account

# We need to get a list of the accounts to then add as members. This actually comes from the Organizations API which we now have access to as a Delegated Admin Child
aws organizations list-accounts | jq '[ .Accounts[] | { AccountId: .Id, Email: .Email } ]' > ACCOUNT_INFO.txt

REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text`
for r in $REGIONS ; do
  echo "Enabling SecurityHub Delegated Admin in $r"

  # Enable Security Hub in this delegated Admin account
  aws securityhub enable-security-hub --no-enable-default-standards --output text --region $r

  sleep 10

  # Update the org config to auto-enable new accounts
  aws securityhub update-organization-configuration --auto-enable --region $r

  # Add all of the existing accounts
  aws securityhub create-members --account-details file://ACCOUNT_INFO.txt --region $r

  # Configure the Consolidated controls and enable all the controls for the enabled frameworks
  aws securityhub update-security-hub-configuration --auto-enable-controls --control-finding-generator SECURITY_CONTROL --region $r
done

# cleanup
rm ACCOUNT_INFO.txt