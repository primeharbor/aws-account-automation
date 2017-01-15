from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import os
import json
import csv
from time import sleep
import datetime
import dateutil.parser
import sys


# These should be passed in via Lambda Environment Variables
try: 
    BLACKHOLE_GROUPNAME = os.environ['BLACKHOLE_GROUPNAME']
    ACTION_TOPIC_ARN = os.environ['ACTION_TOPIC_ARN']
    GRACE_PERIOD = int(os.environ['GRACE_PERIOD'])
    WARN_ONLY = os.environ['WARN_ONLY']
    EMAIL_USERS = os.environ['EMAIL_USERS']
    FROM_ADDRESS = os.environ['FROM_ADDRESS']
    EXPLANATION_FOOTER = os.environ['EXPLANATION_FOOTER']
    EXPLANATION_HEADER = os.environ['EXPLANATION_HEADER']
except KeyError as e:
    print("Key Error: " + e.message)
    sys.exit(1)


# Define a Global String to be the report output sent to ACTION_TOPIC_ARN
ACTION_SUMMARY = ""

print('Loading function')

if WARN_ONLY == "true":
    expired_message = "\n\tYour Password is {} days post expiration. You must change your password or risk losing access. "
    key_expired_message = "\n\tYour AccessKey ID {} is {} days post expiration. You must rotate this key or it will be deactivated. "
else:
    expired_message = "\n\tYour Password is {} days post expiration. Your permissions have been revoked. "
    key_expired_message = "\n\tYour AccessKey ID {} is {} days post expiration. It has been deactivated. "

key_warn_message = "\n\tYour AccessKey ID {} is {} days from expiration. You must rotate this key or it will be deactivated. "
password_warn_message = "\n\tYour Password will expire in {} days"

email_subject = "Credential Expiration Notice From {}"

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, sort_keys=True))
    iam_client = boto3.client('iam')

    try: 
        if event['source'] == "aws.iam" : 
            process_IAMEvent(event, context, iam_client)
        else:
            process_UsersCron(iam_client)
    except KeyError as e:
        # Probably called as a test event with out a source. This is what we want to do here. 
        process_UsersCron(iam_client)
    return


def process_UsersCron(iam_client): 
    global ACTION_SUMMARY 
    max_age = get_max_password_age(iam_client)
    account_name = iam_client.list_account_aliases()['AccountAliases'][0]
    credential_report = get_credential_report(iam_client)
    for row in credential_report:
        if row['password_enabled'] != "true": continue # Skip IAM Users without passwords

        message = ""
        # Process their password
        password_expires = days_till_expire(row['password_last_changed'], max_age)
        if password_expires <= 0:
            message = message + expired_message.format(password_expires * -1)
            add_user_to_blackhole(row['user'], iam_client)
        elif password_expires < GRACE_PERIOD :
            message = message + password_warn_message.format(password_expires)

        # Process their Access Keys
        response = iam_client.list_access_keys( UserName=row['user'] )
        for key in response['AccessKeyMetadata'] :
            key_expires = days_till_expire(key['CreateDate'], max_age)
            if key_expires <= 0:
                message = message + key_expired_message.format(key['AccessKeyId'], key_expires)
                disable_users_key(key['AccessKeyId'], row['user'], iam_client)
            elif key_expires < GRACE_PERIOD:
                message = message + key_warn_message.format(key['AccessKeyId'], key_expires)
        if message != "":
            # print("Message to {}:\n{}".format(row['user'], message)) # Log The message regardless
            if EMAIL_USERS == "true": 
                result = email_user(row['user'], message, account_name)
                if result != "":
                    ACTION_SUMMARY = ACTION_SUMMARY + "\n" + result

    # All Done. Send a summary to the ACTION_TOPIC_ARN, and print one out for the Lambda Logs
    print("Action Summary:" + ACTION_SUMMARY)
    if ACTION_SUMMARY != "": send_summary()
    return

def email_user(email, message, account_name):
    client = boto3.client('ses')
    body = EXPLANATION_HEADER + "\n" + message + "\n\n" + EXPLANATION_FOOTER
    try: 
        response = client.send_email(
            Source=FROM_ADDRESS,
            Destination={ 'ToAddresses': [ email ] },
            Message={
                'Subject': { 'Data': email_subject.format(account_name) },
                'Body': { 'Text': { 'Data': body } }
            }
        )
        return "Email Sent to {}".format(email)
    except ClientError as e:
        print("Failed to send message to {}: {}".format(email, e.message))
        return "Message to {} was rejected: {}".format(email, e.message)

def days_till_expire(last_changed, max_age):
    # Ok - So last_changed can either be a string to parse or already a datetime object.
    # Handle these accordingly
    if type(last_changed) is str:
        last_changed_date=dateutil.parser.parse(last_changed).date()
    elif type(last_changed) is datetime.datetime:
        last_changed_date=last_changed.date()
    else:
        # print("last_changed", last_changed)
        # print(type(last_changed))
        return -99999
    expires = (last_changed_date + datetime.timedelta(max_age)) - datetime.date.today()
    return(expires.days)



def get_credential_report(iam_client):
    resp1 = iam_client.generate_credential_report()
    if resp1['State'] == 'COMPLETE' :
        try: 
            response = iam_client.get_credential_report()
            credential_report_csv = response['Content']
            # print(credential_report_csv)
            reader = csv.DictReader(credential_report_csv.splitlines())
            # print(reader.fieldnames)
            credential_report = []
            for row in reader:
                credential_report.append(row)
            return(credential_report)
        except ClientError as e:
            print("Unknown error getting Report: " + e.message)
    else:
        sleep(2)
        return get_credential_report(iam_client)

def get_max_password_age(iam_client):
    try: 
        response = iam_client.get_account_password_policy()
        return response['PasswordPolicy']['MaxPasswordAge']
    except ClientError as e:
        print("Unexpected error in get_max_password_age: %s" + e.message) 


def process_IAMEvent(event, context, iam_client):

    api_call = event['detail']['eventName']
    if api_call == "CreateLoginProfile" :
        process_CreateLoginProfile(event,context)
        return 0
    elif api_call == "EnableMFADevice" :
        process_EnableMFADevice(event,context)
        return 0
    elif api_call == "DeactivateMFADevice" :
        process_DeactivateMFADevice(event,context)
        return 0
    else:
        raise Exception("Invalid API Call: " + api_call)

def add_user_to_blackhole(username, iam_client):
    if WARN_ONLY == "true": return
    global ACTION_SUMMARY
    ACTION_SUMMARY = ACTION_SUMMARY + "\nAdding {} to Blackhole Group".format(username)
    return
    # response = iam_client.add_user_to_group(
    #     GroupName=os.environ['BLACKHOLE_GROUPNAME'],
    #     UserName=username
    # )
    # if response['ResponseMetadata']['HTTPStatusCode'] != 200:
    #     handle_error("Adding User to Blackhole Group", username, response['ResponseMetadata'])
    # else: 
    #     return 0

def disable_users_key(AccessKeyId, UserName, iam_client):
    if WARN_ONLY == "true": return
    global ACTION_SUMMARY
    ACTION_SUMMARY = ACTION_SUMMARY + "\nDisabling AccessKeyId {} for user {}".format(AccessKeyId, UserName)
    # response = iam_client.update_access_key(
    #     UserName=UserName,
    #     AccessKeyId=AccessKeyId,
    #     Status='Inactive'
    # )
    # if response['ResponseMetadata']['HTTPStatusCode'] != 200:
    #     handle_error("Adding User to Blackhole Group", username, response['ResponseMetadata'])
    # else: 
    #     return 0

def remove_user_from_blackhole(username, iam_client):
    response = iam_client.remove_user_from_group(
        GroupName=os.environ['BLACKHOLE_GROUPNAME'],
        UserName=username
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        handle_error("Removing User from Blackhole Group", username, response['ResponseMetadata'])
    else: 
        return 0

def handle_error(action, username, ResponseMetadata):
    raise Exception("ERROR" + action + " User: " + username + " Details: " + ResponseMetadata)

def send_summary():
    global ACTION_SUMMARY
    client = boto3.client('sns')

    message = "The following Actions were taken by the Expire Users Script at {}: ".format( datetime.datetime.now() ) + ACTION_SUMMARY

    response = client.publish(
        TopicArn=ACTION_TOPIC_ARN,
        Message=message,
        Subject="Expire Users Report for {}".format(datetime.date.today())
    )





