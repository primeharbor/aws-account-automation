#!/usr/bin/env python3
# Copyright 2022 Chris Farris <chrisf@primeharbor.com>
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

import boto3
from botocore.exceptions import ClientError
import json
import os
import time
from datetime import datetime, timezone, date
from dateutil import tz
import datetime as dt
import urllib3

import logging
logger = logging.getLogger()
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', default='INFO')))
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

METRIC="BlendedCost"

def get_webhook(secret_name):
  if secret_name == "NONE":
    return(None)
  client = boto3.client('secretsmanager')
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

WEBHOOK=get_webhook(os.getenv('WEBHOOK', default='NONE'))

def lambda_handler(event, context):
    logger.debug("Received event: " + json.dumps(event, sort_keys=True))

    THRESHOLD_PCT=float(event['alert_percent']) / 100

    cost_alerts = []
    slack_fields = []
    slack_text = ""

    try:
        ce_client = boto3.client('ce')

        # Get the dates for the CostExplorer Calls
        today = date.today()
        yesterday = today - dt.timedelta(days=1)
        one_week_ago = today - dt.timedelta(days=8)
        start_of_this_month = today.replace(day=1)
        end_of_last_month = start_of_this_month - dt.timedelta(days=1)
        start_of_last_month = end_of_last_month.replace(day=1)

        # Get per-service costs
        alert_args = {
            "TimePeriod": {'Start': str(one_week_ago), 'End': str(yesterday) },
            "Metrics": [METRIC],
            "Granularity": 'DAILY',
            "Filter": {"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Usage"] }},
            "GroupBy": [{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
        }

        if 'services' in event:
            alert_args['Filter'] = {
                "And": [
                    {"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Usage"] }},
                    {"Dimensions": {"Key": "SERVICE", "Values": event['services'] }}
                ]
            }
        response = ce_client.get_cost_and_usage(**alert_args)

        # Go though the data
        last_week_cost_data = response['ResultsByTime'][0]['Groups']
        today_cost_data = response['ResultsByTime'][-1]['Groups']

        last_week_costs = {}
        for c in last_week_cost_data:
            last_week_costs[c['Keys'][0]] = round(float(c['Metrics'][METRIC]['Amount']), 2)

        todays_costs = {}
        for c in today_cost_data:
            todays_costs[c['Keys'][0]] = round(float(c['Metrics'][METRIC]['Amount']), 2)

        for key, amount in todays_costs.items():
            if key not in last_week_costs:
                logger.debug(f"Key {key} not in last_week_costs")
                continue

            cost_diff = round(amount - last_week_costs[key], 2)
            if last_week_costs[key] != 0:
                cost_diff_pct = round(cost_diff/last_week_costs[key], 2)
            else:
                cost_diff_pct = 0

            if 'all' in event and event['all'] is True:
                if last_week_costs[key] == 0 and amount == 0:
                    continue
                cost_alerts.append(f"{key} Cost-per-day Last Week: ${last_week_costs[key]:,} ; Cost-per-day Today: ${amount:,} ; Difference: ${cost_diff} USD ({round(cost_diff_pct*100)}%)")
                slack_fields.append({"title": key, "value": f"Today:       ${amount:,}\nLast Week: ${last_week_costs[key]:,}\n Difference: {round(cost_diff_pct*100)}%", "short": True})

            elif cost_diff > float(event['threshold']) and cost_diff_pct > THRESHOLD_PCT:
                    cost_alerts.append(f"{key} Cost-per-day Last Week: ${last_week_costs[key]:,} ; Cost-per-day Today: ${amount:,} ; Difference: ${cost_diff} USD ({round(cost_diff_pct*100)}%)")
                    slack_fields.append({"title": key, "value": f"Today:       ${amount:,}\nLast Week: ${last_week_costs[key]:,}\n Difference: {round(cost_diff_pct*100)}%", "short": True})

        # Get the total overall cost by day
        response = ce_client.get_cost_and_usage(
            TimePeriod={'Start': str(one_week_ago), 'End': str(yesterday) },
            Metrics=[METRIC],
            Granularity='DAILY',
            Filter={"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Usage"] }},
        )

        last_week_total_cost = round(float(response['ResultsByTime'][0]['Total'][METRIC]['Amount']),2)
        today_total_cost = round(float(response['ResultsByTime'][-1]['Total'][METRIC]['Amount']),2)
        cost_diff = round(today_total_cost-last_week_total_cost,2)
        cost_diff_pct = round(cost_diff/today_total_cost,2)
        slack_text += f"Total Cost per day Last Week:   ${last_week_total_cost:,}\n"
        slack_text += f"Cost per day Today:             ${today_total_cost:,}\n"
        slack_text += f"Difference (week over week):    ${cost_diff:,} ({round(cost_diff_pct*100)}%)\n"

        # Total Spent Month To Date
        response = ce_client.get_cost_and_usage(
            TimePeriod={'Start': str(start_of_last_month), 'End': str(today) },
            Metrics=[METRIC],
            Granularity='MONTHLY',
            Filter={"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Usage"] }},
            # GroupBy=[{'Type': 'DIMENSION', 'Key': 'RECORD_TYPE'}],
        )

        lastmonth_total_cost = round(float(response['ResultsByTime'][0]['Total'][METRIC]['Amount']),2)
        thismonth_total_cost = round(float(response['ResultsByTime'][-1]['Total'][METRIC]['Amount']),2)
        slack_text += f"Total Spent month-to-date:      ${thismonth_total_cost:,}\n"
        slack_text += f"Last Month Total:               ${lastmonth_total_cost:,}\n"

        if 'credits' in event and event['credits'] is True:
            # Total Credits Month To Date
            response = ce_client.get_cost_and_usage(
                TimePeriod={'Start': str(start_of_last_month), 'End': str(today) },
                Metrics=[METRIC],
                Granularity='MONTHLY',
                Filter={"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Credit"] }},
                # GroupBy=[{'Type': 'DIMENSION', 'Key': 'RECORD_TYPE'}],
            )
            lastmonth_total_credit = round(float(response['ResultsByTime'][0]['Total'][METRIC]['Amount']),2)
            thismonth_total_credit = round(float(response['ResultsByTime'][-1]['Total'][METRIC]['Amount']),2)
            slack_text += f"Total Credits month-to-date:    ${thismonth_total_credit:,}\n"
            slack_text += f"Last Month Credits:             ${lastmonth_total_credit:,}\n"

        if WEBHOOK is not None:
            fields = [
                {"title": "Total Cost per day Last Week:", "value": f"${last_week_total_cost:,}", "short": False},
                {"title": "Cost per day Today:          ", "value": f"${today_total_cost:,}", "short": False},
                {"title": "Difference (week over week): ", "value": f"${cost_diff:,} ({round(cost_diff_pct*100)}%)", "short": False},
                {"title": "Total Spent month-to-date    ", "value": f"${thismonth_total_cost:,}", "short": False},
                {"title": "Last Month Total Spend:      ", "value": f"${lastmonth_total_cost:,}", "short": False}
            ]

            total_attachment = {
              'pretext': f"*Total Spend For: {os.environ['ACCOUNT_NAME']}*",
              'title': f"Service Usage as of {yesterday}",
              'fields': fields,
              'mrkdwn_in': ["pretext", "text"],
              'color': '#7CD197'
            }

            slack_message = {
                'text': f"Billing anomaly report for {yesterday}",
                'attachments': [total_attachment],
                'username': "BillingMetrics",
                'mrkdwn': True,
                'icon_emoji': ':moneybag:'
            }

            if len(slack_fields) != 0:
                attachment = {
                  'pretext': f"*Cost Spikes for: {os.environ['ACCOUNT_NAME']}*",
                  'title': f"Service Usage as of {yesterday}",
                  'fields': slack_fields,
                  'mrkdwn_in': ["pretext", "text"],
                  'color': '#ff0000'
                }
                slack_message['attachments'].append(attachment)

            logger.debug(json.dumps(slack_message, sort_keys=True, default=str, indent=2))
            try:
                http = urllib3.PoolManager()
                r = http.request('POST', WEBHOOK, body=json.dumps(slack_message))
                logger.info("Message posted to slack")
            except Exception as e:
                logger.error(f"Slack Request failed: {e}")
                raise
        else:
            for a in cost_alerts:
                print(a)
            print(slack_text)

    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException':
            logger.error(f"AccessDeniedException for cost-explorer")
            return()
        else:
            logger.critical(f"AWS Error getting info: {e}")
            raise
    except Exception as e:
        raise
## End of Function Code ##


def do_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')
    parser.add_argument("--timestamp", help="Output log with timestamp and toolname", action='store_true')
    parser.add_argument("--all", help="Print All Cost Data, regardless of size or Difference", action='store_true')
    parser.add_argument("--credits", help="Show Credits too", action='store_true')
    parser.add_argument("--threshold", help="Ignore Service costs below this threshold", default=100.0, type=float)
    parser.add_argument("--alert-percent", help="Only report if the cost exceeds this percent", default=10.0, type=float)
    args = parser.parse_args()
    return(args)

if __name__ == '__main__':

    args = do_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        os.environ['LOG_LEVEL'] = "DEBUG"
    elif args.error:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)


    # create formatter
    if args.timestamp:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        formatter = logging.Formatter('%(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)


    event = {
        "threshold": args.threshold,
        "alert_percent": args.alert_percent,
        "all": args.all,
        "credits": args.credits,
        "services": [
            "AWS Backup",
            "AWS CloudTrail",
            "AWS Config",
            "AWS Direct Connect",
            "AWS Firewall Manager",
            "AWS Network Firewall",
            "AWS Security Hub",
            "AWS Service Catalog",
            "AWS Shield",
            "Amazon Detective",
            "Amazon GuardDuty",
            "Amazon Inspector",
            "Amazon Macie",
            "CloudWatch Events"
        ]
    }

    try:
        return_event = lambda_handler(event, {})
        # print(json.dumps(return_event, indent=2))
    except KeyboardInterrupt:
        exit(1)
