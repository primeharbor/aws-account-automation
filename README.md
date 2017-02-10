# aws-account-automation
Tools to Automate your AWS Account

* DeployBucketTemplate will create a Bucket for lambda or other package deployments. It can be configured to allow access via http from your VPC endpoints or corporate network

* AccountAlertTopics will create three SNS Topics (Critical, Error, Info) and export the ARNs to be used in other templates. It can optionally deploy a lambda that will push the published messages to a slack channel

* IAM-Expire-Users will deploy a lambda that will SES notify users when their API Keys or password are about to expire and can be configured to disable their account, or deactivate their key if they're older than the accounts age in the password policy

* CloudTrailTemplate will deploy CloudTrail to your account along with all the necessary sub-parts including the Logging Bucket, KMS Key and CloudWatch Logs Group

* requireMFA-Template will deploy a IAM User Group and Lambda that will prevent users without MFA from doing anything in the account