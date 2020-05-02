# aws-account-automation
Tools to Automate your AWS Account


* [AccountAlertTopics](AccountAlertTopics.md) will create three SNS Topics (Critical, Error, Info) and stack export them to be used in other templates. It can optionally deploy a lambda that will push the published messages to a slack channel

* [AuditRole](cloudformation/AuditRole-Template.yaml) creates a generic security auditor role for an account. [Deploy QuickLink](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateUrl=https%3A%2F%2Fs3.amazonaws.com%2Fpht-cloudformation%2Faws-account-automation%2FAuditRole-Template.yaml&stackName=SecurityAuditRole&param_RoleName=Auditor)

* [BillingBucket](cloudformation/BillingBucket-Template.yaml) creates a bucket in your payer account for billing reports and applies the appropriate Bucket Policy. [Deploy QuickLink](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateUrl=https%3A%2F%2Fs3.amazonaws.com%2Fpht-cloudformation%2Faws-account-automation%2FBillingBucket-Template.yaml&stackName=BillingBucket&param_pCreateBucket=true)

* [CloudTrailTemplate](cloudformation/CloudTrail-Template.yaml) creates a [CloudTrail](https://aws.amazon.com/cloudtrail/) following industry best practices. It creates the S3 bucket, a Customer Managed Key for the events, enables log validation and multi-region support and will send events to CloudWatch Logs. [Deploy QuickLink](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateUrl=https%3A%2F%2Fs3.amazonaws.com%2Fpht-cloudformation%2Faws-account-automation%2FCloudTrail-Template.yaml&stackName=CloudTrail&param_pCloudTrailLogGroupName=CloudTrail%2FDefaultLogGroup&param_pCreateBucket=true&param_pCreateTopic=true)

* [CloudWatch Alarms for CloudTrail API Activity](cloudformation/CloudWatchAlarmsForCloudTrailAPIActivity-Template.yaml) Deploys multiple CloudWatch Alarms for CloudTrail events that happen in your account. Requires CloudTrail to be feeding a LogGroup and the [AccountAlertTopics](AccountAlertTopics.md) stack to be deployed.



* [requireMFA](cloudformation/requireMFA-Template.yaml) will deploy a IAM User Group and Lambda that will prevent users without MFA from doing anything in the account


## Hosting
The most recent version of all these templates are hosted in S3 for Easy Deployment.

Directly callable URLS:
* https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/AccountAlertTopics-Template.yaml
* https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/AuditRole-Template.yaml
* https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/BillingBucket-Template.yaml
* https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/CloudTrail-Template.yaml
* https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/CloudWatchAlarmsForCloudTrailAPIActivity-Template.yaml
* https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/EBSAutomatedTagging.yaml
* https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/IAM-ExpireUsers-Template.yaml
* https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/requireMFA-Template.yaml


