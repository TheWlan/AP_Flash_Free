'''------------------------------------------------------------------
    script: AP-flash-chk.py
    author: Haydn Andrews
    date:   1/7/2019
    desc:   Find APs with Flash corruption, it will use threading to test multiple APs at
            Same Time
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
from netmiko import ConnectHandler

def config_worker(device):
    file = open("ap-flash-chk-result.csv", "a")
    error = "Error"
    print("Testing AP: " + device)
    try:
        net_connect = ConnectHandler(ip=device, device_type='cisco_ios', username='admin', password='P@ssword1',
                                     secret="P@ssword1", timeout=20, auth_timeout=20)
        #net_connect = ConnectHandler(ip=device, device_type='cisco_ios', username='admin', password='#Fr3shFo0dP3opL3*',
                                    # secret="#Fr3shFo0dP3opL3*", timeout=20, auth_timeout=20)
        time.sleep(1)
        net_connect.enable()
        CDPOUT = net_connect.send_command("dir flash:", delay_factor=2,
                                          use_textfsm=True)  # BW-Added textfsm start
        #print(CDPOUT) #Print the output for checking
        js_CDPOUT = CDPOUT
        
        with open('APSpace.json', 'a') as outfile:
            json.dump(js_CDPOUT, outfile)
            
            for neighbor in CDPOUT:
                test = (neighbor['name'],neighbor['total_free'])
                   
            net_connect.disconnect()
            #print(test[1])
            Flash_free = int(test[1])
            if Flash_free <= 18141185:
                print("AP IP: " + device + " Does not have enough Flash Storage Free")
                print(Flash_free)
                file.write(device + "," + str(Flash_free) + ",Not_Enough_Space\n")  # Write to user friendly CSV
            else:
                print('enough flash')
                print(Flash_free)
                file.write(device + "," + str(Flash_free) + ",Enough_Space\n")  # Write to user friendly CSV
        ####################################################################
        # Login and test if AP has Flash Corruption if first attempt fails
        ####################################################################
    except:
        try:
            net_connect = ConnectHandler(ip=device, device_type='cisco_ios', username='admin',
                                         password='pythonP@ssword1', secret="P@ssword1", timeout=20,
                                         auth_timeout=20)
           # net_connect = ConnectHandler(ip=device, device_type='cisco_ios', username='admin',
                                        # password='#Fr3shFo0dP3opL3*', secret="#Fr3shFo0dP3opL3*", timeout=20,
                                        # auth_timeout=20)
            time.sleep(1)
            net_connect.enable()
            CDPOUT = net_connect.send_command("dir flash:", delay_factor=2,
                                          use_textfsm=True)  # BW-Added textfsm start
        # print(CDPOUT) #Print the output for checking
            js_CDPOUT = CDPOUT
            
            with open('APSpace.json', 'a') as outfile:
                json.dump(js_CDPOUT, outfile)
                
                print(type(CDPOUT))

                for neighbor in CDPOUT:
                    test = (neighbor['name'],neighbor['total_free'])
                    
                net_connect.disconnect()
                Flash_free = int(test[1])
                if Flash_free <= 18141185:
                    print("AP IP: " + device + " Does not have enough Flash Storage Free")
                    print(Flash_free)
                    file.write(device + "," + str(Flash_free) + ",Not_Enough_Space\n")  # Write to user friendly CSV
                else:
                    print('enough flash')
                    print(Flash_free)
                    file.write(device + "," + str(Flash_free) + ",Enough_Space\n")
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
            devices[device['AP']] = device  # For Non WOW Customers

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