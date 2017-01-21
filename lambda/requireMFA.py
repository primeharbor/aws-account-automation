from __future__ import print_function

import json
import boto3
import sys
import os

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, sort_keys=True))

    # Error Checking goes first
    if event['source'] != "aws.iam" : sys.exit(0)

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

def process_CreateLoginProfile(event, context):
    # Get the important bits
    username = event['detail']['responseElements']['loginProfile']['userName']
    
    # Verify there is no MFA present
    client = boto3.client('iam')
    response = client.list_mfa_devices( UserName=username )

    if len(response['MFADevices']) == 0 :
        # There is no MFA enabled
        print (username + " does not have MFA. Adding to blackhole Group")
        add_user_to_blackhole(username)
    else :
        print (username + " has an MFA. Removing from blackhole Group")
        remove_user_from_blackhole(username)
    print("CreateLoginProfile Execution Complete")

def process_EnableMFADevice(event, context):
    # Get the important bits
    username = event['detail']['requestParameters']['userName']

    # Verify there is an MFA present
    client = boto3.client('iam')
    response = client.list_mfa_devices( UserName=username )
    if len(response['MFADevices']) >= 1 :
        # There is now an MFA
        print (username + " has activated their MFA. Removing from blackhole Group")
        remove_user_from_blackhole(username)
    else :
        print (username + " has no MFA. Adding to blackhole Group")
        add_user_to_blackhole(username)
    print("EnableMFADevice Execution Complete")

def process_DeactivateMFADevice(event, context):
    # Get the important bits
    username = event['detail']['requestParameters']['userName']
    
    # Verify there is no MFA present
    client = boto3.client('iam')
    response = client.list_mfa_devices( UserName=username )

    if len(response['MFADevices']) == 0 :
        # There is no MFA enabled
        print (username + " does not have MFA. Adding to blackhole Group")
        add_user_to_blackhole(username)
    else :
        print (username + " has an MFA. Removing from blackhole Group")
        remove_user_from_blackhole(username)
    print("DeactivateMFADevice Execution Complete")

def add_user_to_blackhole(username):
    client = boto3.client('iam')
    response = client.add_user_to_group(
        GroupName=os.environ['BLACKHOLE_GROUPNAME'],
        UserName=username
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        handle_error("Adding User to Blackhole Group", username, response['ResponseMetadata'])
    else: 
        return 0

def remove_user_from_blackhole(username):
    client = boto3.client('iam')
    response = client.remove_user_from_group(
        GroupName=os.environ['BLACKHOLE_GROUPNAME'],
        UserName=username
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        handle_error("Removing User from Blackhole Group", username, response['ResponseMetadata'])
    else: 
        return 0

def handle_error(action, username, ResponseMetadata):
    raise Exception("ERROR" + action + " User: " + username + " Details: " + ResponseMetadata)
