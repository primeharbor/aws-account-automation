# aws-account-automation
Tools to Automate your AWS Account

* DeployBucketTemplate will create a Bucket for lambda or other package deployments. It can be configured to allow access via http from your VPC endpoints or corporate network

* AccountAlertTopics will create three SNS Topics (Critical, Error, Info) and export the ARNs to be used in other templates. It can optionally deploy a lambda that will push the published messages to a slack channel

* IAM-Expire-Users will deploy a lambda that will SES notify users when their API Keys or password are about to expire and can be configured to disable their account, or deactivate their key if they're older than the accounts age in the password policy

* CloudTrailTemplate will deploy CloudTrail to your account along with all the necessary sub-parts including the Logging Bucket, KMS Key and CloudWatch Logs Group

* requireMFA-Template will deploy a IAM User Group and Lambda that will prevent users without MFA from doing anything in the account


## Hosting
The most recent version of all these templates are hosted in S3 for Easy Deployment.

* [Deploy CloudTrail Template](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?filter=active&templateURL=https:%2F%2Fs3.amazonaws.com%2Froom17-automation-artifacts%2Fpublic%2FCloudTrailTemplate.yaml&stackName=admin-CloudTrail&param_pCloudTrailLogGroupName=CloudTrail%2FDefaultLogGroup&param_pCreateBucket=false&param_pCreateTopic=true)
* [Bucket for Billing Reports](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?filter=active&templateURL=https%3A%2F%2Fs3.amazonaws.com%2Froom17-automation-artifacts%2Fpublic%2FBillingBucket.yaml&stackName=admin-BillingBucket&param_pCreateBucket=true)
* [AccountAlertTopics](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?filter=active&templateURL=https%3A%2F%2Fs3.amazonaws.com%2Froom17-automation-artifacts%2Fpublic%2FAccountAlertTopics-Template.yaml&stackName=account-alert-topics&pDeployLambda=true)
* [CloudTrail Alarms](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?filter=active&templateURL=https%3A%2F%2Fs3.amazonaws.com%2Froom17-automation-artifacts%2Fpublic%2FCloudWatch_Alarms_for_CloudTrail_API_Activity.yaml&stackName=account-cloudtrail-alarms)
* [RequireMFA](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?filter=active&templateURL=https%3A%2F%2Fs3.amazonaws.com%2Froom17-automation-artifacts%2Fpublic%2FCloudWatch_Alarms_for_CloudTrail_API_Activity.yaml&stackName=account-RequireMFA)

## URLS
* https://s3.amazonaws.com/room17-automation-artifacts/public/AccountAlertTopics-Template.yaml
* https://s3.amazonaws.com/room17-automation-artifacts/public/BillingBucket.yaml
* https://s3.amazonaws.com/room17-automation-artifacts/public/CloudTrailTemplate.yaml
* https://s3.amazonaws.com/room17-automation-artifacts/public/CloudWatch_Alarms_for_CloudTrail_API_Activity.yaml
* https://s3.amazonaws.com/room17-automation-artifacts/public/DeployBucketTemplate.yaml
* https://s3.amazonaws.com/room17-automation-artifacts/public/requireMFA-Template.yaml





