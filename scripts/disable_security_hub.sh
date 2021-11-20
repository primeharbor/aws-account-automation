#!/bin/bash

PROFILE=""

if [ ! -z "$1" ] ; then
	PROFILE="--profile $1"
fi

REGIONS=`aws ec2 describe-regions --query 'Regions[].[RegionName]' --output text  $PROFILE`
for r in $REGIONS ; do
  echo "Disabling Security Hub in ${r}"
  aws securityhub disable-security-hub --region $r  $PROFILE
done