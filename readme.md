# XIQ Duplicate AP Check
##### XIQ_Duplicate_AP_Check.py
### <span style="color:purple">Purpose</span>
This script will check for devices with duplicate hostnames. If found, it will check if either of them are managed but unconnected. If found the device will be unmanaged and added to a ccg and added to json list with an expiration time of 30 days. Once the expiration time runs out the device will be deleted from XIQ. 

## <span style="color:purple">Setting up the script</span>
At the top of the script there are some variables that need to be added.
1. <span style="color:purple">XIQ_API_token</span> - Update this with a valid token. The token will need the device and ccg permissions
2. <span style="color:purple">ccg_groupn</span> - The name of the CCG that will be used for duplicate devices that are unmananged
> NOTE: The following proxyDict variable is in the app/xiq_api.py script
3. <span style="color:purple">proxyDict</span> - if a proxy is used you can fill out the http and https to be used. 
```
proxyDict = {
            "http": "",
            "https": ""
        }
```
## Needed files
the XIQ_Duplicate_AP_Check.py script uses several other files. If these files are missing the script will not function.
In the same folder as theXIQ_Duplicate_AP_Check.py script there should be an /app/ folder. Inside this folder should be a logger.py file and a xiq_api.py file. After running the script a new file 'Duplicate_AP_log.log' will be created. Another file, monitor_unmanaged.json is used to track the expire time of devices that have been moved to the unmanaged state. If this file does not exist it will be created. If the file exist but is not a json file the script will fail. 


The log file that is created when running will show any errors that the script might run into. It is a great place to look when troubleshooting any issues. The log file will also include the device ids for devices that are  unmanaged and deleted.

## Running the script
open the terminal to the location of the script and run this command.

```
python XIQ_Duplicate_AP_Check.py
```

## requirements
There are additional modules that need to be installed in order for this script to function. They are listed in the requirements.txt file and can be installed with the command 'pip install -r requirements.txt' if using pip.