# aws-account-automation
Tools to Automate your AWS Account


* [AccountAlertTopics](AccountAlertTopics.md) will create three SNS Topics (Critical, Error, Info) and stack export them to be used in other templates. It can optionally deploy a lambda that will push the published messages to a slack channel

* [AuditRole](cloudformation/AuditRole-Template.yaml) creates a generic security auditor role for an account. [QuickLink Deploy](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateUrl=https%3A%2F%2Fs3.amazonaws.com%2Fpht-cloudformation%2Faws-account-automation%2FAuditRole-Template.yaml&stackName=SecurityAuditRole&param_RoleName=Auditor)

* [BillingBucket](cloudformation/BillingBucket-Template.yaml) creates a bucket in your payer account for billing reports and applies the appropriate Bucket Policy. [QuickLink Deploy](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateUrl=https%3A%2F%2Fs3.amazonaws.com%2Fpht-cloudformation%2Faws-account-automation%2FBillingBucket-Template.yaml&stackName=BillingBucket&param_pCreateBucket=true)

* [CloudTrailTemplate](cloudformation/CloudTrail-Template.yaml) creates a [CloudTrail](https://aws.amazon.com/cloudtrail/) following industry best practices. It creates the S3 bucket, a Customer Managed Key for the events, enables log validation and multi-region support and will send events to CloudWatch Logs. [QuickLink Deploy](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateUrl=https%3A%2F%2Fs3.amazonaws.com%2Fpht-cloudformation%2Faws-account-automation%2FCloudTrail-Template.yaml&stackName=CloudTrail&param_pCloudTrailLogGroupName=CloudTrail%2FDefaultLogGroup&param_pCreateBucket=true&param_pCreateTopic=true)

* [CloudWatchAlarmsForCloudTrailAPIActivity](cloudformation/CloudWatchAlarmsForCloudTrailAPIActivity-Template.yaml) Deploys multiple CloudWatch Alarms for CloudTrail events that happen in your account. Requires CloudTrail to be feeding a LogGroup and the [AccountAlertTopics](AccountAlertTopics.md) stack to be deployed. [QuickLink Deploy](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateUrl=https%3A%2F%2Fs3.amazonaws.com%2Fpht-cloudformation%2Faws-account-automation%2FCloudWatchAlarmsForCloudTrailAPIActivity-Template.yaml&stackName=CloudTrailAlarms&param_pDashboardName=Security&param_pLogGroupName=CloudTrail%2FDefaultLogGroup&param_pParanoiaLevel=TopicAlertsParanoid)

* [EBSAutomatedTagging](cloudformation/EBSAutomatedTagging.yaml) - probably not useful since AWS will autotag EBS volumes now
* [IAM-ExpireUsers](cloudformation/IAM-ExpireUsers-Template.yaml) - Work in progress to automatically handle users that have not changed their password or rotated access keys
* [requireMFA](cloudformation/requireMFA-Template.yaml) will deploy a IAM User Group and Lambda that will prevent users without MFA from doing anything in the account

* [SESRuleToSlack](cloudformation/SESRuleToSlack-Template.yaml) Creates and SES Email receiving rule/rulset to accept all email for a domain, invoke a lambda function that sends a summary of the email to Slack. Useful for when you might get an important notice, but you don't really need to interact from a domain.


:exclamation: **Also check out the [aws-fast-fixes python scripts](https://github.com/WarnerMedia/aws-fast-fixes) for manual security fixes for your account!** :exclamation:


## Hosting
The most recent version of all these templates are hosted in S3 for Easy Deployment. You can find the latest HTTP URL, S3 URL, QuickDeploy Links and HTTP URLs for previous versions in the [Links.md](Links.md) file.

