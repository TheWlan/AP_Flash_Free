'''------------------------------------------------------------------
    script: AP-flash-free.py
    author: Haydn Andrews
    date:   1/7/2019
    desc:   Find APs with less than 18MB of free flash
	Requirements:
	    - You need to have this: git clone https://github.com/networktocode/ntc-templates.git
        - You need File with each APs IP address listed per line
          called "ap-flash-chk.txt" in directory this script is run from

    modification history:
    what    when            who     why
    v0.1    1/7/2019        HA      Initial version
-------------------------------------------------------------------'''
import json
import os
#from pprint import pprint # used if debugging
import time
from multiprocessing.dummy import Pool as ThreadPool
from napalm import get_network_driver
from netmiko import ConnectHandler
from netmiko import Netmiko

""" Variables - Either a file or define in a function """
username_variable = 'admin'
password_variable = 'P@ssword1'
enable_password_variable = 'P@ssword1'
transport_variable = 'ssh'
fast_cli_variable = False    # Saves 8 seconds connecting

def config_worker(device):
    file = open("ap-flash-chk-result.csv", "a")
    error = "Error"
    Flash_free = {}
    print("Testing AP: " + device)
    try:
        """ Napalm connect """
        driver = get_network_driver('ios')
        optional_args = {'transport': transport_variable, 'secret': enable_password_variable, 'fast_cli': fast_cli_variable}
        dev = driver(device, username_variable, password_variable, timeout=30, optional_args=optional_args)
        dev.open()

        CDPOUT = dev.device.send_command("dir flash:", delay_factor=2,
                                          use_textfsm=True)  # BW-Added textfsm start
        #print(CDPOUT) #Print the output for checking
        js_CDPOUT = CDPOUT
        
        with open('APSpace.json', 'a') as outfile:
            json.dump(js_CDPOUT, outfile)
            
            for neighbor in CDPOUT:
                Flash_free = {"name":(neighbor['name']), "Free": (neighbor['total_free'])}
                   
            dev.close()

            if int(Flash_free["Free"]) <= 18000000:
                print("AP IP: " + device + " Does not have enough Flash Storage Free")
                print(Flash_free["Free"])
                file.write(device + "," + test + ",Not_Enough_Space\n")  # Write to user friendly CSV
            else:
                print('enough flash')
                print(Flash_free["Free"])
                print("test")
                file.write(device + "," + test + ",Enough_Space\n")  # Write to user friendly CSV
        ####################################################################
        # Login and test if AP has Flash Corruption if first attempt fails
        ####################################################################
    except:
        try:
            """ Napalm connect """
            driver = get_network_driver('ios')
            optional_args = {'transport': transport_variable, 'secret': enable_password_variable, 'fast_cli': fast_cli_variable}
            dev = driver(device, username_variable, password_variable, timeout=30, optional_args=optional_args)
            dev.open()

            CDPOUT = dev.device.send_command("dir flash:", delay_factor=2,
                                          use_textfsm=True)  # BW-Added textfsm start
        # print(CDPOUT) #Print the output for checking
            js_CDPOUT = CDPOUT
            
            with open('APSpace.json', 'a') as outfile:
                json.dump(js_CDPOUT, outfile)

                for neighbor in CDPOUT:
                    Flash_free = {"name":(neighbor['name']), "Free": (neighbor['total_free'])}
                       
                dev.close()

                if int(Flash_free["Free"]) <= 18000000:
                    print("AP IP: " + device + " Does not have enough Flash Storage Free")
                    print(Flash_free["Free"])
                    file.write(device + "," + test + ",Not_Enough_Space\n")  # Write to user friendly CSV
                else:
                    print('enough flash')
                    print(Flash_free["Free"])
                    print("test")
                    file.write(device + "," + test + ",Enough_Space\n")  # Write to user friendly CSV
        ##################################
        # If AP not online
        ##################################
        except:
            output = "Host down: " + device
            print(output)
            file = open("wow-ap-flash-chk-down.txt", "a")
            file.write(output)
            file.close()

    return

def read_devices(devices_filename):
    devices = {}  # create our dictionary for storing devices and their info

    with open(devices_filename) as devices_file:
        for device_line in devices_file:
            device_info = device_line.strip().split(',')  # extract device info from line

            device = {'AP': device_info[0]}  # create dictionary of device objects ...
            #devices[device['AP'][0]+ device['AP'][2:]] = device  # store our device in the devices dictionary - Woolworths Only As applies NAT
            devices[device['AP']] = device  # No NAT


    return devices

#######################################################
# ---- Main: Get Configuration
#######################################################

devices = read_devices('ap-flash-chk.txt')

#Ask number of threads to use - Default 5
num_threads_str = input('\nNumber of threads (5): ') or '5'
num_threads = int(num_threads_str)

config_params_list = []
for AP, device in devices.items():
   # print('Creating thread for: ' + AP)
    config_params_list.append((AP))

starting_time = time.time()

print('\n--- Creating threadpool, launching check for Flash Free Space\n')
threads = ThreadPool(num_threads)
results = threads.map(config_worker, config_params_list)

threads.close()
threads.join()

print('\n---- End get config threadpool, elapsed time=', time.time() - starting_time)

######################################################
# Clean up the JSON Output File to correct formating
######################################################
exists = os.path.isfile('./APSpace.json') # Check the JSON File Exists, will only be created if APs in Flash Corruption State
if exists:
    with open('APSpace.json', 'r') as file :
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace('][', ',')

    # Write the file out again
    with open('APSpace.json', 'w') as file :
        file.write(filedata)
else:
    print("No APs in Flash Corruption Issue")