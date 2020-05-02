# AccountAlertTopics

This template creates three SNS topics in your account for Critical, Error and Info Alerts. It can additionally deploy a Lambda to send messages to a Slack Webhook (stored in Secrets Manager).

The three SNS Topic are exported from this template and can be leveraged with the ImportValue feature in cloudformation. Those exports are:
* SNSAlertsCriticalArn
* SNSAlertsErrorArn
* SNSAlertsInfoArn

You must specifiy an email and SMS number. The email will be subscribed to all three topics, and the SMS number will be subscribed to the Critical Topic

## Deploy

1. Create a Secret for your Slack Webhook
```json
{"webhook_url": "https://hooks.slack.com/services/THISPARTISSECRET"}
```
2. Deploy from the [quicklink](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateUrl=https%3A%2F%2Fs3.amazonaws.com%2Fpht-cloudformation%2Faws-account-automation%2FAccountAlertTopics-Template.yaml&stackName=AccountAlertTopics&param_pAccountDescription=ENTER%20ACCOUNT%20NAME&param_pAlarmEmoji=%3Aalert%3A&param_pBillingThreshold=0&param_pDeploySlackLambda=yes&param_pIconEmoji=%3Acloud%3A&param_pInitialSubscriberEmail=ENTER-YOUR-EMAIL&param_pInitialSubscriberSMS=ENTER-YOUR-CELL&param_pOkEmoji=%3Agreen_check%3A&param_pSlackChannel=%23aws_notices&param_pSlackWebhookSecret=NAME%20of%20SECRET)

Or you can deploy it via the Direct Link to S3: https://s3.amazonaws.com/pht-cloudformation/aws-account-automation/AccountAlertTopics-Template.yaml
