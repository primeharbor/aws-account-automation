# Lambda to tag EBS Volumes with Event Info
from __future__ import print_function
import boto3
import json
import logging
import sys
import os
from botocore.exceptions import ClientError
import datetime

try: 
  TAG_PREFIX = os.environ['TAG_PREFIX'] + "-"
except KeyError as e:
  print("Key Error: " + e.message)
  sys.exit(1)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client('ec2')

 
# Lambda main routine
def lambda_handler(event, context):
  logger.info("Received event: " + json.dumps(event, sort_keys=True))

  # Error Checking goes first
  if event['source'] == "aws.ec2" : 
    api_call = event['detail']['eventName']
    volume_id = event['detail']['responseElements']['volumeId']
    username = get_username(event['detail']['userIdentity']['arn'])
    if api_call == "CreateVolume" :
      process_CreateVolume(event,volume_id, username)
      return 0
    elif api_call == "AttachVolume" :
      process_AttachVolume(event,volume_id, username)
      return 0
    elif api_call == "RunInstances" :
      process_RunInstances(event, username)
      return 0
    elif api_call == "DetachVolume" :
      process_DetachVolume(event,volume_id, username)
      return 0        
    else:
      logger.error("Invalid API Call: " + api_call)
      return 0
  elif event['source'] == "aws.events" :
    process_on_schedule()
  else:
    logger.error("Received Event Source no supported: " + event['source'])

# End lambda_handler()


#
# functions in response to events
#
def process_DetachVolume(event,volume_id, username):
  #
  # Capture who did the detach and when
  #
  logger.info("user: " + username + " detached Volume " + volume_id )
  try: 
    response = client.create_tags(
      Resources=[ volume_id ],
      Tags=[ 
        { 'Key': TAG_PREFIX + 'detached_by', 'Value': username },
        { 'Key': TAG_PREFIX + 'detached_date', 'Value':  event['detail']['eventTime'] }
      ]
    )
  except ClientError as e:
    logger.error("unable to tag volume " + volume_id + " with username " + username + ": " + e.message )
# end process_DetachVolume()

def process_CreateVolume(event,volume_id, username):
  #
  # Capture who created the volume
  #
  logger.info("user: " + username + " created Volume " + volume_id )
  try: 
    response = client.create_tags(
      Resources=[ volume_id ],
      Tags=[ { 'Key': TAG_PREFIX + 'created_by', 'Value': username }, ]
    )
  except ClientError as e:
    logger.error("unable to tag volume " + volume_id + " with username " + username + ": " + e.message )
# end process_CreateVolume()

def process_AttachVolume(event,volume_id, username):
  #
  # If explictly attached, capture the who, what and when. Also remove detachment details
  #
  instance_id = event['detail']['responseElements']['instanceId']
  logger.info("user: " + username + " attached Volume " + volume_id + " to "+ instance_id + " as " + event['detail']['responseElements']['device'])
  tag_volume("attached", volume_id, username, instance_id, event['detail']['responseElements']['device'], event['detail']['eventTime'] )
  # Remove detachment info
  try: 
    response = client.delete_tags( Resources=[ volume_id ], Tags=[{ 'Key': TAG_PREFIX + 'detached_by' }, { 'Key': TAG_PREFIX + 'detached_date'} ])
  except ClientError as e:
    logger.error("unable to delete detachment info from " + volume_id + ": " + e.message )
# end process_AttachVolume()

def process_RunInstances(event, username):
  #
  # If an instance is created, capture details of all the attached volumes (including the root volume)
  #
  # We can have multiple Instances started in a single event
  for i in event['detail']['responseElements']['instancesSet']['items']:
    instance = get_instance(i['instanceId'])
    for device in instance['BlockDeviceMappings']:
        tag_volume("attached", device['Ebs']['VolumeId'], username, i['instanceId'], device['DeviceName'], device['Ebs']['AttachTime'].isoformat())
# end process_RunInstances()


def process_on_schedule():
  #
  # Run this regularly to keep things up-to-date
  #

  # FIXME - support more than 500 volumes
  response = client.describe_volumes(
    Filters=[ { 'Name': 'status', 'Values': [ 'in-use' ] },
    ],
    # NextToken='string',
    MaxResults=500
  )

  for v in response['Volumes']: 
    v_id = v['VolumeId']
    a = v['Attachments'][0]
    try: 
      t = tags_to_hash(v['Tags'])

      if a['InstanceId'] not in t[TAG_PREFIX + 'attached_to_instance'] or a['Device'] not in t[TAG_PREFIX + 'attached_to_instance'] :
        try: 
          name = tags_to_hash(get_instance(a['InstanceId'])['Tags'])['Name']
        except KeyError :
          name = "untagged"

        value = a['InstanceId'] + " (" + name + ") as " + a['Device']
        modify_tag(v_id, TAG_PREFIX + 'attached_to_instance', value )
      
    except KeyError as e:
      # There are no tags, lets just apply some
      try: 
        name = tags_to_hash(get_instance(a['InstanceId'])['Tags'])['Name']
      except KeyError :
        name = "untagged"
      value = a['InstanceId'] + " (" + name + ") as " + a['Device']
      modify_tag(v_id, TAG_PREFIX + 'attached_to_instance', value )



  return 0
## end process_on_schedule()

#
# Helper functions
# 

# Convert Instance tags to a hash
def tags_to_hash(key_values):
  output = {}
  for i in key_values:
    output[i['Key']] = i['Value']
  return output

# Modify a specific tag for a specific volume
def modify_tag(volume_id, key, value):
  try: 
    response = client.create_tags(
      Resources=[ volume_id ],
      Tags=[{ 'Key': key, 'Value': value }])
    logger.info("Set " + key + " to " + value + " for " + volume_id)
  except ClientError as e:
    logger.error("unable to tag volume " + volume_id + " with username " + username + ": " + e.message )  

# Assumed Roles don't follow the same conventions as IAM users. This should cover both
def get_username(arn):
  return(arn.split(':')[-1])

# Get the details of an instance    
def get_instance(id):
  response = client.describe_instances( InstanceIds=[ id ] )
  return(response['Reservations'][0]['Instances'][0])

# Tag a specific volume with all the tags of an event
def tag_volume(verb, volume_id, username, instance_id, device, attachment_time): 
  try: 
    response = client.create_tags(
      Resources=[ volume_id ],
      Tags=[{ 'Key': TAG_PREFIX + verb + '_by', 'Value': username },
            { 'Key': TAG_PREFIX + verb + '_to_instance', 'Value': instance_id },
            { 'Key': TAG_PREFIX + verb + '_as_device', 'Value': device },
            { 'Key': TAG_PREFIX + verb + '_date', 'Value':  attachment_time} ])
  except ClientError as e:
    logger.error("unable to tag volume " + volume_id + " with username " + username + ": " + e.message )

#### END OF FUNCTION CODE ###