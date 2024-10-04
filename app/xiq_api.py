#!/usr/bin/env python3
import logging
import os
import inspect
import sys
import json
import time
import requests
from pprint import pprint as pp
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from requests.exceptions import HTTPError, ReadTimeout
from app.logger import logger
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger('PSK_Rotator.xiq_api')

PATH = current_dir

class APICallFailedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class XIQ:
    def __init__(self, user_name=None, password=None, token=None):
        self.URL = "https://api.extremecloudiq.com"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.proxyDict = {
            "http": "",
            "https": ""
        }
        self.totalretries = 5
        if token:
            self.headers["Authorization"] = "Bearer " + token
        else:
            try:
                self.__getAccessToken(user_name, password)
            except ValueError as e:
                print(e)
                raise SystemExit
            except HTTPError as e:
               print(e)
               raise SystemExit
            except:
                log_msg = "Unknown Error: Failed to generate token for XIQ"
                logger.error(log_msg)
                print(log_msg)
                raise SystemExit 
    #API CALLS
    def __get_api_call(self, url):
        try:
            response = requests.get(url, headers= self.headers, verify=False, proxies=self.proxyDict)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if response.status_code != 200:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                else:
                    logger.warning(f"\n\n{data}")
            raise APICallFailedException(log_msg) 
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
            raise APICallFailedException("Unable to parse the data from json, script cannot proceed")
        return data
    
    def __put_api_call(self, url, payload):
        try:
            response = requests.put(url, headers= self.headers, data=payload, verify=False, proxies=self.proxyDict)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if response.status_code != 200:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                else:
                    logger.warning(f"{data}")
            raise APICallFailedException(log_msg) 
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
            raise APICallFailedException("Unable to parse the data from json, script cannot proceed")
        return data

    def __post_api_call(self, url, payload):
        try:
            response = requests.post(url, headers= self.headers, data=payload, verify=False, proxies=self.proxyDict)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise ValueError(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if response.status_code == 202:
            return response.status_code
        elif response.status_code != 200 and response.status_code != 201:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                    raise APICallFailedException(data['error_message'])
            raise APICallFailedException(log_msg)
        if response.text:
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
                raise APICallFailedException("Unable to parse the data from json, script cannot proceed")
            return data
        else:
            return response.status_code
        
    def __delete_api_call(self, url):
        try:
            response = requests.delete(url, headers= self.headers, verify=False, proxies=self.proxyDict)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise ValueError(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if response.status_code == 202:
            return response.status_code
        elif response.status_code != 200 and response.status_code != 201:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                    raise APICallFailedException(data['error_message'])
            raise APICallFailedException(log_msg)
        if response.text:
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
                raise APICallFailedException("Unable to parse the data from json, script cannot proceed")
            return data
        else:
            return response.status_code
      
    def __getAccessToken(self, user_name, password):
        info = "get XIQ token"
        success = 0
        url = self.URL + "/login"
        payload = json.dumps({"username": user_name, "password": password})
        try:
            data = self.__post_api_call(url=url,payload=payload)
        except APICallFailedException as e:
            print(f"API to {info} failed with {e}")
            print('script is exiting...')
            raise SystemExit
        except:
            print(f"API to {info} failed with unknown API error")
        else:
            success = 1
        if success != 1:
            print("failed to get XIQ token. Cannot continue to import")
            print("exiting script...")
            raise SystemExit
        
        if "access_token" in data:
            #print("Logged in and Got access token: " + data["access_token"])
            self.headers["Authorization"] = "Bearer " + data["access_token"]
            return 0

        else:
            log_msg = "Unknown Error: Unable to gain access token for XIQ"
            logger.warning(log_msg)
            raise ValueError(log_msg)

        
    
    # Devices
    ## Check for config mismatches
    def collectDevices(self, pageSize=100, location_id=None):
        info = "to collect devices" 
        page = 1
        pageCount = 1
        firstCall = True
        devices = []
        while page <= pageCount:
            url = f"{self.URL}/devices?views=FULL&page={str(page)}&limit={str(pageSize)}"
            if location_id:
                url = url  + "&locationId=" +str(location_id)
            try:
                rawList = self.__get_api_call(url)
            except APICallFailedException as e:
                raise APICallFailedException(e)
            devices = devices + rawList['data']

            if firstCall == True:
                pageCount = rawList['total_pages']
            print(f"completed page {page} of {rawList['total_pages']} collecting Devices")
            page = rawList['page'] + 1 
        return devices

    ##Unmanage devices
    def unmanageDevices(self,device_ids:list):
        url = f"{self.URL}/devices/:unmanage"
        payload = json.dumps({
          "ids": device_ids
        })
        try:
            response = self.__post_api_call(url,payload)
        except APICallFailedException as e:
                raise APICallFailedException(e)
        logger.info(f"Successfully unmanaged devices: {', '.join(map(str, device_ids))}")
        return "Success"    
    
    def deleteDevices(self,device_ids:list):
        url = f"{self.URL}/devices/:delete"
        payload = json.dumps({
          "ids": device_ids
        })
        try:
            response = self.__post_api_call(url,payload)
        except APICallFailedException as e:
                raise APICallFailedException(e)
        logger.info(f"Successfully deleted devices: {', '.join(map(str, device_ids))}")
        return "Success" 
    
    # CCG
    ## Check if CCG group exists
    def checkForCCG(self,ccg_name,pageSize=100):
        info = "collecting CCGs"
        page = 1
        pageCount = 1
        firstCall = True
        ccgs = []
        while page <= pageCount:
            url = f"{self.URL}/ccgs?page={str(page)}&limit={str(pageSize)}"
            try:
                rawList = self.__get_api_call(url)
            except APICallFailedException as e:
                raise APICallFailedException(e)
            ccg_match = next((d for d in rawList['data'] if d.get("name") == ccg_name), None)
            if ccg_match:
                return True, ccg_match
            ccgs = ccgs + rawList['data']
            if firstCall == True:
                pageCount = rawList['total_pages']
            # check for ccg_name
            
            print(f"completed page {page} of {rawList['total_pages']} collecting CCGs")
            page = rawList['page'] + 1 
        return False, {}
    
    ## Create CCG group
    def createCCG(self, data):
        url = f"{self.URL}/ccgs"
        try:
            response = self.__post_api_call(url,payload=json.dumps(data))
        except APICallFailedException as e:
            raise APICallFailedException(e)
        logger.info(f"Successfully created ccg: {data['name']} with devices: {', '.join(map(str, data['device_ids']))}")
        return response['id']

    # Update CCG group
    def updateCCG(self, ccg_id, device_ids):
        url = f"{self.URL}/ccgs/{ccg_id}"
        payload = json.dumps({"device_ids": device_ids})
        try:
            response = self.__put_api_call(url,payload=payload)
        except APICallFailedException as e:
            raise APICallFailedException(e)
        logger.info(f"Successfully added devices to ccg: {', '.join(map(str, device_ids))}")
        return response['id']
    
    def deleteCCG(self, ccg_id):
        url = f"{self.URL}/ccgs/{ccg_id}"
        try:
            response = self.__delete_api_call(url)
        except APICallFailedException as e:
            raise APICallFailedException(e)
        logger.info(f"Successfully deleted ccg")
        return "Success"
