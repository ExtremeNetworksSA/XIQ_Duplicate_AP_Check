#!/usr/bin/env python3
import logging
import os
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from pprint import pprint as pp
from app.xiq_api import XIQ, APICallFailedException
from app.logger import logger
logger = logging.getLogger("Duplicate_Check.Main")

PATH = os.path.dirname(os.path.abspath(__file__))

token = ''
if not token:
    print("Please add a token to the script.")
    print("Script is exiting...")
    raise SystemExit

# CCG Group Name
ccg_group = "MarkedAsReplaced"

# JSON for unmanaged devices with removal dates
unmanaged_file = f'{PATH}/monitor_unmanaged.json'

# Function to remove the expired devices
def removeExpiredDevices(expired_device_list):
    log_msg = f"The following devices will be deleted from XIQ as they have reached expiration date: {', '.join(map(str, expired_device_list))}"
    logger.info(log_msg)
    print(log_msg)
    try:
        status = x.deleteDevices(expired_device_list)
    except APICallFailedException as e:
        print(f"API call failed to unmanage device with {str(e)}.")
        print("Script is exiting...")
        raise SystemExit
    if status == "Success":
        return status
    else:
        raise APICallFailedException(f"{status} to delete devices.")

def checkCCG():
    ## check if CCG group exists
    try:
        ccg_found, ccg_info = x.checkForCCG(ccg_name=ccg_group)
    except APICallFailedException as e:
        print(f"API to find CCG {ccg_group} failed with {str(e)}.")
        print("Script is exiting...")
        raise SystemExit
    return ccg_found, ccg_info

#collect time info
now = datetime.now()
one_month = now + timedelta(days=30)
current_time = time.mktime(now.timetuple())
expire_time = time.mktime(one_month.timetuple())

# check if json file exists
if os.path.exists(unmanaged_file):
    with open(unmanaged_file) as FH:
        unmanaged_list = json.load(FH)
else:
    print(f"{unmanaged_file} file not found")
    unmanaged_list = []

json_file_change = False

# Establish connection to XIQ
x = XIQ(token=token)

# collect all devices in XIQ
devices = x.collectDevices()
df = pd.DataFrame(devices)

# filter out just duplicate named devices
duplicated_rows = df[df.duplicated(subset='hostname', keep=False)]

# check if CCG exists and get information
ccg_found, ccg_info = checkCCG()

# check for devices that time has run out
expired_devices = [] # list for devices that are expired
not_found_devices = [] # list for devices that no longer exist in XIQ
for device in unmanaged_list:
    if any( d['id'] == device['device_id'] for d in devices):
        if device['expire_at'] <= current_time:
            expired_devices.append(device['device_id'])
    else:
        logger.info(f"device {device['device_id']} no longer exists in XIQ. Device will be removed from json file.")
        not_found_devices.append(device['device_id'])
if expired_devices:
    try:
        status = removeExpiredDevices(expired_devices)
    except APICallFailedException as e:
        logger.error(e)
        print(e)
        print("Script is exiting...")
        raise SystemExit
    unmanaged_list = [device for device in unmanaged_list if device["device_id"] not in expired_devices]
    ccg_info['device_ids'] = [device_id for device_id in ccg_info['device_ids'] if device_id not in expired_devices]
    json_file_change = True

if not_found_devices:
    unmanaged_list = [device for device in unmanaged_list if device["device_id"] not in not_found_devices]
    json_file_change = True

if duplicated_rows.empty:
    print("No Duplicate APs name found")
    if ccg_found and not ccg_info['device_ids']:
        # Delete ccg
        try:
            status = x.deleteCCG(ccg_info['id'])
        except APICallFailedException as e:
            logger.error(e)
            print(e)
            print("Script is exiting...")
            raise SystemExit
        log_msg = (f"deleted CCG {ccg_info['name']} as no devices exist.")
        logger.info(log_msg)
        print(log_msg)
    raise SystemExit 

unique_device_names = duplicated_rows['hostname'].unique()

device_ids = []
new_devices = []

for device_name in unique_device_names:
    filt = (duplicated_rows['hostname'] == device_name) & \
           ((duplicated_rows['connected'] == False) & (duplicated_rows['device_admin_state'] == 'MANAGED')) 
    device_ids.extend(duplicated_rows.loc[filt,'id'].astype(int).tolist())
        
if device_ids:
    # Unmanage offline duplicate devices 
    try:
        status = x.unmanageDevices(device_ids)
    except APICallFailedException as e:
        print(f"API call failed to unmanage device with {str(e)}.")
        print("Script is exiting...")
        raise SystemExit

    if status != "Success":
        log_msg = f"Unmange API did not return a Success message!"
        logger.error(log_msg)
        print(log_msg)
        print("script is exiting...")
        raise SystemExit
    
    # add devices to CCG group
    if not ccg_found:
        # create CCG with the devices
        data = {
          "name": ccg_group,
          "description": "CCG for Unmanaged Duplicate APs",
          "device_ids": device_ids
        }
        try:
            ccg_id = x.createCCG(data)
        except APICallFailedException as e:
            print(f"API to create CCG {ccg_group} failed with {str(e)}.")
            print("Script is exiting...")
            raise SystemExit
        if ccg_id:
            log_msg = f"Successfully created CCG {ccg_id}"
            logger.info(log_msg)
            print(log_msg)
            logger.info(f"Added devices {', '.join(map(str, device_ids))} to ccg {ccg_group}")
    else:
        # add devices to existing CCG
        ccg_id = ccg_info['id']
        ccg_devices = ccg_info['device_ids']
        common_devices = set(ccg_devices) & set(device_ids)
        if common_devices:
            log_msg = (f"These devices are already in the {ccg_group} CCG: {', '.join(map(str, common_devices))}")
            logger.info(log_msg)
            print(log_msg)
        device_ids = [device for device in device_ids if device not in ccg_devices]
        ccg_devices.extend(device_ids)
        try:
            response = x.updateCCG(ccg_id, ccg_devices)   
        except APICallFailedException as e:
            print(f"API to update CCG {ccg_group} failed with {str(e)}.")
            print("Script is exiting...")
            raise SystemExit
        log_msg = f"Successfully updated CCG {ccg_group}"
        logger.info(log_msg)
        print(log_msg)
        logger.info(f"Added devices {', '.join(map(str, device_ids))} to ccg {ccg_group}")

    

    new_devices = [{"device_id": device_id, "added_time":current_time, "expire_at": expire_time} for device_id in device_ids ]
    json_file_change = True
    
else:
    print("No Duplicates with one being managed and offline") 
    #check if any ccg devices not in unmanaged_list
    if ccg_found and ccg_info['device_ids']:
        untracked_devices = [device_id for device_id in ccg_info['device_ids'] if not any(device_id == d['device_id'] for d in unmanaged_list)]
        if untracked_devices:
            log_msg = f"The following devices are in the CCG, but not in the unmanaged json file. No action will be preformed on these APs. {', '.join(map(str, untracked_devices))}"
            logger.warning(log_msg)
            print(log_msg)
    # remove CCG if no devices
    else:
        # Delete ccg
        if ccg_found:
            try:
                status = x.deleteCCG(ccg_info['id'])
            except APICallFailedException as e:
                logger.error(e)
                print(e)
                print("Script is exiting...")
                raise SystemExit
            logger.info(f"deleted CCG {ccg_info['name']} as no devices exist.")
        logger.info(f"CCG {ccg_group} does not exist.")
        
# if changes to unamanged_list save the json file
if json_file_change:
    unmanaged_list.extend(new_devices)
    with open(unmanaged_file, "w") as FH:
        json.dump(unmanaged_list, FH)


