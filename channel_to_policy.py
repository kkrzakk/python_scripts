#!/usr/bin/env python3

"""Script allows to add/remove notification channels from alert policies"""

#TODO: clean up script
#TODO: check where you can improve the code
# imports
import argparse
from google.cloud import monitoring_v3
from google.protobuf import field_mask_pb2 as field_mask

# Arguments parser

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--channel", help="specify notification channels to add(Display Name)")
    parser.add_argument("-i", "--project_id", help="specify project id(default projects/<setup_project>)",
                        default="projects/<setup_project>")
    parser.add_argument(
        "-p", "--policy", help="specify policies to exclude(Display Name)")
    parser.add_argument("-d", "--delete", action='store_true',
                        help="flag notfication channels for deletion")
    parser.add_argument("--dryrun", action="store_true",
                        help="shows what changes will take place")
    args = parser.parse_args()
    project_id = args.project_id
    channels = []
    excluded_policies = []
    delete = args.delete
    dryrun = args.dryrun
    try:
        channels = args.channel.strip().split(',')
    except Exception:
        pass
    try:
        excluded_policies = args.policy.strip().split(',')
    except Exception:
        pass
    return project_id, channels, excluded_policies, delete, dryrun

# Get selected notification channels


def get_selected_channels(project_name, selected_channels):
    client = monitoring_v3.NotificationChannelServiceClient()
    channels = client.list_notification_channels(name=project_name)
    global channels_dict
    channels_dict = {}
    channels_final = []
    for channel in channels:
        channels_dict[channel.display_name] = channel.name.split('/')[-1]
    if selected_channels:
        for channel in selected_channels:
            if channel in channels_dict:
                channels_final.append(channels_dict[channel])
    return channels_final

# adds existing channels to inputed channels


def add_exisitng_channels(channels, extra_channels, deletion):
    if deletion:
        for channel in channels:
            try:
                extra_channels.remove(channel)
            except Exception:
                pass
        return list(dict.fromkeys(extra_channels))
    else:
        for channel in extra_channels:
            channels.append(channel)
    return list(dict.fromkeys(channels))

# Get every policy id, clean them and exclude


def get_selected_policies(project_name, excluded_policies=[]):
    client = monitoring_v3.AlertPolicyServiceClient()
    policies = client.list_alert_policies(name=project_name)
    selected_policies = {}
    policies_channels = {}
    for policy in policies:
        policies_channels[policy.display_name] = clean_numbers(
            str(policy.notification_channels))
        selected_policies[policy.display_name] = policy.name.split('/')[-1]
    for excluded_policy in excluded_policies:
        try:
            del selected_policies[excluded_policy]
        except Exception:
            pass
    return selected_policies, policies_channels

# clean data


def clean_numbers(data):
    data = data.split("'")
    data = data[1::2]
    result = []
    for i in data:
        i = i.split('/')[-1]
        result.append(i)
    return result

# for every policy change notification channels


def modify_policies(project_name, channels, policies, policies_channels, deletion, dryrun):
    for key in policies:
        replace_notification_channels(
            project_name, policies[key], channels, policies_channels, key, deletion, dryrun)
    return


def replace_notification_channels(project_name, alert_policy_id, channel_ids, policies_channels, key, deletion, dryrun):
    _, project_id = project_name.split("/")
    alert_client = monitoring_v3.AlertPolicyServiceClient()
    channel_client = monitoring_v3.NotificationChannelServiceClient()
    policy = monitoring_v3.AlertPolicy()
    display_name = policy.display_name
    policy.name = alert_client.alert_policy_path(project_id, alert_policy_id)
    channels_modified = add_exisitng_channels(
        channel_ids, policies_channels[key], deletion)
    if not dryrun:
        for channel_id in channels_modified:
            policy.notification_channels.append(
                channel_client.notification_channel_path(
                    project_id, channel_id)
            )

        mask = field_mask.FieldMask()
        mask.paths.append("notification_channels")
        updated_policy = alert_client.update_alert_policy(
            alert_policy=policy, update_mask=mask
        )
        print("Updated", updated_policy.name)
    else:
        dryrun_message(key, channels_modified, channel_ids, deletion)

# Message for dryrun - get channels ids and using global variables print display names


def dryrun_message(name, channels, input_channels, deletion):
    channels_list = []
    channels_input = []
    for channel in channels:
        channels_list.append(list(channels_dict.keys())[
                             list(channels_dict.values()).index(channel)])
    for channel in input_channels:
        channels_input.append(list(channels_dict.keys())[
            list(channels_dict.values()).index(channel)])
    print("Policy: {}".format(name))
    print("Notification Channels:")
    if deletion:
        print("(-)", end=" ")
        print(*channels_input, sep=(", "))
        print("After changes: ")
        print(*channels_list, sep=(", "))
        print("---------------------------------")
    else:
        print("(+) {}", end=" ")
        print(*channels_input, sep=(", "))
        print("After changes: ")
        print(*channels_list, sep=(", "))
        print("---------------------------------")

# Main


def main():
    project_id, channels, excluded_policies, deletion, dryrun = parse_args()
    channels = get_selected_channels(project_id, channels)
    policies, policies_channels = get_selected_policies(
        project_id, excluded_policies)
    modify_policies(project_id, channels, policies,
                    policies_channels, deletion, dryrun)


if __name__ == "__main__":
    main()
