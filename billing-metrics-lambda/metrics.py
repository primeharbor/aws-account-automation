#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
import json
import os
import time
import datetime
import urllib3
# import pytz

import logging
logger = logging.getLogger()
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', default='INFO')))
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

def get_webhook(secret_name):
  client = boto3.client('secretsmanager', region_name=os.environ['WEBHOOK_REGION'])
  try:
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
  except ClientError as e:
    logger.critical(f"Unable to get secret value for {secret_name}: {e}")
    return(None)
  else:
    if 'SecretString' in get_secret_value_response:
      secret_value = get_secret_value_response['SecretString']
    else:
      secret_value = get_secret_value_response['SecretBinary']
  try:
    secret_dict = json.loads(secret_value)
    return(secret_dict['webhook_url'])
  except Exception as e:
    logger.critical(f"Error during Credential and Service extraction: {e}")
    raise

WEBHOOK=get_webhook(os.environ['WEBHOOK'])
http = urllib3.PoolManager()


def lambda_handler(event, context):
  '''Find and process all the CloudWatch Alarms in ALARM State'''
  logger.debug("Received event: " + json.dumps(event, sort_keys=True))

  client = boto3.client('cloudwatch')

  metric_name = "EstimatedCharges"
  stat = "Maximum"
  # eastern = pytz.timezone('US/Eastern')
  total = None

  metrics = []
  fields = []
  response = client.list_metrics(MetricName=metric_name)
  while 'NextToken' in response:  # Gotta Catch 'em all!
    metrics += response['Metrics']
    response = client.list_metrics(MetricName=metric_name, NextToken=response['NextToken'])
  metrics += response['Metrics']

  logger.debug(f"Found {len(metrics)} metrics for {metric_name}")

  for m in metrics:
    response = client.get_metric_statistics(
      Namespace=m['Namespace'],
      MetricName=metric_name,
      Dimensions=m['Dimensions'],
      StartTime=datetime.datetime.now() - datetime.timedelta(hours=26),
      EndTime=datetime.datetime.now(),
      Period=300,
      Statistics=[stat]
    )
    datapoints = response['Datapoints']

    if len(datapoints) == 0:
      logger.warning(f"get_metric_statistics return no results for {m}")
      continue

    sorted_datapoints = sorted(datapoints, key = lambda i: i['Timestamp'], reverse=True)
    m['LatestDataPoint'] = sorted_datapoints[0]
    m['YesterdayDataPoint'] = sorted_datapoints[-1]
    m['Dimensions'] = munge_dimensions(m['Dimensions'])
    logger.debug(f"Most Recent Datapoint for {metric_name} in is {m} ")

    if 'ServiceName' not in m['Dimensions']:
      # This is the total bill
      total = m['LatestDataPoint'][stat]
      total_diff = round(m['LatestDataPoint'][stat] - m['YesterdayDataPoint'][stat], 2)
      timestamp = m['LatestDataPoint']['Timestamp']
    else:
      if m['LatestDataPoint'][stat] == 0:
        continue
      diff = round(m['LatestDataPoint'][stat] - m['YesterdayDataPoint'][stat], 2)
      fields.append({"title": m['Dimensions']['ServiceName'], "value": f"US$ {m['LatestDataPoint'][stat]} (+ ${diff})", "short": True})

  if total is not None:
    attachment = {
      'fallback': f"Billing update for {os.environ['ACCOUNT_NAME']}",
      'pretext': f"*Estimated Charges for Acct: {os.environ['ACCOUNT_NAME']}*",
      'title': f"Service Usage as of {timestamp}",
      'text': f"*Total Bill:* US${total} +(${total_diff})",
      'fields': fields,
      'mrkdwn_in': ["pretext", "text"],
      'color': '#7CD197'
    }
    slack_text = ""
  else:
    attachment = {}
    slack_text = "No billing info available"

  slack_message = {
    'channel': os.environ['SLACK_CHANNEL'],
    'text': slack_text,
    'attachments': [attachment],
    'username': "BillingMetrics",
    'mrkdwn': True,
    'icon_emoji': ':moneybag:'
  }

  logger.debug(json.dumps(slack_message, sort_keys=True, default=str, indent=2))
  try:
    r = http.request('POST', WEBHOOK, body=json.dumps(slack_message))
    logger.info("Message posted to %s", slack_message['channel'])
  except Exception as e:
    logger.error(f"Request failed: {e}")

def munge_dimensions(dimensions_array):
    output = {}
    for d in dimensions_array:
        output[d['Name']] = d['Value']
    return(output)


if __name__ == '__main__':

    # Process Arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')


    args = parser.parse_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    if args.debug:
        ch.setLevel(logging.DEBUG)
    elif args.error:
        ch.setLevel(logging.ERROR)
    else:
        ch.setLevel(logging.INFO)
    # create formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    # Wrap in a handler for Ctrl-C
    try:
        rc = lambda_handler({}, {})
        print("Lambda executed with {}".format(rc))
    except KeyboardInterrupt:
        exit(1)