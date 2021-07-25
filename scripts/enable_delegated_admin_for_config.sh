#!/bin/bash

#
# Script to configure AWS Config Service for Delegated Admin.
# This script should be run in the AWS Organizations Management (formerly Master) Account
#
# Copyright 2021 Chris Farris <chrisf@primeharbor.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ADMIN=$1

if [ -z "$ADMIN" ] ; then
	echo "$0 <account_id for delegated admin for config>"
	exit 1
fi

aws organizations enable-aws-service-access --service-principal=config-multiaccountsetup.amazonaws.com
aws organizations enable-aws-service-access --service-principal=config.amazonaws.com
aws organizations register-delegated-administrator --account-id $ADMIN --service-principal config-multiaccountsetup.amazonaws.com
aws organizations register-delegated-administrator --account-id $ADMIN --service-principal config.amazonaws.com
aws organizations list-delegated-administrators --service-principal config-multiaccountsetup.amazonaws.com
aws organizations list-delegated-administrators --service-principal config.amazonaws.com
