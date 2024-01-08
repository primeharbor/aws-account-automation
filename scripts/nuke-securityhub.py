#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
# logger = logging.getLogger()


def main(args, logger):
    '''Executes the Primary Logic of the Fast Fix'''

    # If they specify a profile use it. Otherwise do the normal thing
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    # Get all the Regions for this account
    for region in get_regions(session, args):
        sechub_client = session.client("securityhub", region_name=region)
        config_client = session.client("config", region_name=region)

        if args.deregister:
            disable_admin(region, args)

        delete_recorders(config_client, region, args)

        delete_securityhub(sechub_client, region, args)


def disable_admin(region, args):
    client = boto3.client('organizations')
    delegated_id = None
    response = client.list_delegated_administrators()
    for account in response['DelegatedAdministrators']:
        response = client.list_delegated_services_for_account(AccountId=account['Id'])
        for s in response['DelegatedServices']:
            if s['ServicePrincipal'] == 'securityhub.amazonaws.com':
                delegated_id = account['Id']

    if delegated_id is None:
        logger.error(f"Could not find a delegated Administrator for security hub in {region}")
    else:
        if args.actually_do_it:
            logger.info(f"Deregistering {delegated_id} as delegated Administrator in {region}")
            response = client.deregister_delegated_administrator(
                AccountId=delegated_id, ServicePrincipal='securityhub.amazonaws.com')
        else:
            logger.info(f"Would deregister {delegated_id} as delegated Administrator in {region}")


def delete_securityhub(client, region, args):

    try:
        describe_response = client.describe_hub()
    except Exception as e:
        logger.info(f"Security Hub isn't enabled in {region}")
        return(None)

    try:
        response = client.list_configuration_policy_associations()
        for a in response['ConfigurationPolicyAssociationSummaries']:
            if a['TargetType'] == "ACCOUNT":
                target = {'AccountId': a['TargetId']}
            elif a['TargetType'] == "ORGANIZATIONAL_UNIT":
                target = {'OrganizationalUnitId': a['TargetId']}
            else:
                target = {'RootId': a['TargetId']}

            if args.actually_do_it:
                logger.info(f"Starting Policy Disassociation for {a['ConfigurationPolicyId']} on {target} in {region}")
                response = client.start_configuration_policy_disassociation(
                    Target=target,
                    ConfigurationPolicyIdentifier=a['ConfigurationPolicyId']
                )
            else:
                logger.info(f"Would start Policy Disassociation for {a['ConfigurationPolicyId']} on {target} in {region}")


        response = client.list_configuration_policies()
        for p in response['ConfigurationPolicySummaries']:
            if args.actually_do_it:
                logger.info(f"Deleting Config Policy {p['Id']}")
                response = client.delete_configuration_policy(Identifier=p['Id'])
            else:
                logger.info(f"Would Delete Config Policy {p['Id']}")

        if args.actually_do_it:
            logger.info(f"Disabling Central Configuration")
            response = client.update_organization_configuration(
                AutoEnable=False,
                AutoEnableStandards='NONE',
                OrganizationConfiguration={
                    'ConfigurationType': 'LOCAL',
                }
            )
        else:
            logger.info(f"Would disable Central Configuration ")



    except ClientError as e:
        if e.response['Error']['Code'] == "AccessDeniedException":
            logger.debug(f"{e}")
            pass
        else:
            raise

    try:
        response = client.list_members(OnlyAssociated=False)
        account_list = []
        for a in response['Members']:
            account_list.append(a['AccountId'])

        if args.actually_do_it:
            logger.info(f"disassociate_members in {region}")
            response = client.disassociate_members(
                AccountIds=account_list
            )
        else:
            logger.info(f"Would disassociate_members in {region}")
    except ClientError as e:
        if e.response['Error']['Code'] == "BadRequestException":
            logger.warning(f"Account is not Delegated Administrator")
            pass
        elif e.response['Error']['Code'] == "AccessDeniedException":
            logger.warning(f"Didn't disassociate_members in {region}: {e}")
            pass
        else:
            raise

    if args.actually_do_it:
        logger.info(f"Disabing Security Hub in {region}")
        try:
            response = client.disable_security_hub()
        except ClientError as e:
            if e.response['Error']['Code'] == "InvalidInputException":
                logger.warning(f"Cannot Disable Security Hub in {region}: {e}")
                pass
            else:
                raise
    else:
        logger.info(f"Would Disable Security Hub in {region}")




def delete_recorders(client, region, args):
    try:
        response = client.delete_configuration_recorder(ConfigurationRecorderName='Default')
    except ClientError as e:
        if e.response['Error']['Code'] == "NoSuchConfigurationRecorderException":
            logger.info(f"Config is not enabled in {region}")
            pass
        else:
            raise


def get_regions(session, args):
    '''Return a list of regions with us-east-1 first. If --region was specified, return a list wth just that'''

    # If we specifed a region on the CLI, return a list of just that
    if args.region:
        return([args.region])

    # otherwise return all the regions, us-east-1 first
    ec2 = session.client('ec2')
    response = ec2.describe_regions()
    output = ['us-east-1']
    for r in response['Regions']:
        # return us-east-1 first, but dont return it twice
        if r['RegionName'] == "us-east-1":
            continue
        output.append(r['RegionName'])
    return(output)


def do_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')
    parser.add_argument("--region", help="Only Process Specified Region")
    parser.add_argument("--profile", help="Use this CLI profile (instead of default or env credentials)")
    parser.add_argument("--actually-do-it", help="Actually Perform the action", action='store_true')
    parser.add_argument("--deregister", help="Deregister Delegated Administrator (in Management Account)", action='store_true')

    args = parser.parse_args()

    return(args)

if __name__ == '__main__':

    args = do_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    logger = logging.getLogger('nuke-securityhub')
    ch = logging.StreamHandler()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.error:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

    # Silence Boto3 & Friends
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    # create formatter
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    try:
        main(args, logger)
    except KeyboardInterrupt:
        exit(1)