import logging
from urllib3.util import Retry
from requests import Session
from requests.adapters import HTTPAdapter
import requests
import argparse
import netifaces
import subprocess
import sys
import time

def request(method, url, retry=3, **kwargs):
    """Constructs and sends a :class:`Request <Request>`.

    Args:
        method (str):
            method for the new :class:`Request` object:
                `GET`, `OPTIONS`, `HEAD`, `POST`,
                `PUT`, `PATCH`, or `DELETE`.
        url (str): URL for the new :class:`Request` object.
        retry (int, optional):
            The maximum number of retries each connection should attempt.
            Defaults to 3.

    Returns:
        requests.Response: requests.Response
    """
    retries = Retry(total=retry)

    with Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))
        logging.info(f"Send {method} request to {url}")
        logging.debug(f"Request parameter: {kwargs}")

        resp = session.request(method=method, url=url, **kwargs)
        logging.debug(resp.text)
        return resp


def post(url, data=None, json=None, retry=3, **kwargs):
    """Sends a POST request

    Args:
        url (str): URL for the new :class:`Request` object.
        data (dict|list|bytes, optional):
            Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
            Defaults to None.
        json (json, optional):
            A JSON serializable Python object to send in
                the body of the :class:`Request`.
            Defaults to None.
        retry (int, optional):
            The maximum number of retries each connection should attempt.
            Defaults to 3.

    Returns:
        requests.Response: requests.Response
    """
    return request("post", url, data=data, json=json, retry=retry, **kwargs)


def get_ip_mac(interface):
    try:
        # get the mac address
        mac_address = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        
        # get the ip address
        ip_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET)
        if ip_info is not None:
            ip_address = ip_info[0]['addr']
        else:
            ip_address = None
        
        return ip_address, mac_address
    except ValueError as e:
        print(f"Error: {e}")
        return None


# set the rtc wake 
def set_rtc_wake(wake_time):
    # set the wake time
    # command = f"echo {wake_time} > /sys/class/rtc/rtc0/wakealarm"
    # TODO: use check_output and command list
    command = f"rtcwake -m no -s {wake_time}"
    subprocess.run(command, shell=True, check=True)

#try to suspend or power off the system
# TODO: use check_output and command list
def s3_or_s5_system(type): 
    if type == "s3":
        subprocess.run("systemctl suspend", shell=True, check=True)
    elif type == "s5":
        subprocess.run("systemctl poweroff", shell=True, check=True)
    else:
        print("Error: type should be s3 or s5")

#bring up the system by rtc or any other way in case the wake-on-lan failed
def bring_up_system(way, time):
    # try to wake up the system by rtc
    if way == "rtc":
        set_rtc_wake(time)
    else:
        # try to wake up the system by other way
        print("we don't have any way to bring up the system now. Some error happened.")
        #change to sys.exit("dont have")
        system.exit(1)
        
# write the time stamp to a file to store the test start time
def write_timestamp(timestamp_file):
    with open(timestamp_file, "w") as f:
        f.write(str(time.time()))


def main():
    parser = argparse.ArgumentParser(description="Parse command line arguments.")
    
    parser.add_argument("--interface", required=True, help="The network interface to use.")
    parser.add_argument("--target", required=True, help="The target IP address or hostname.")
    parser.add_argument("--delay", type=int, default=60, help="Delay between attempts (in seconds).")
    parser.add_argument("--retry", type=int, default=3, help="Number of retry attempts.")
    parser.add_argument("--waketype", default="g", help="Type of wake operation.")
    parser.add_argument("--powertype", type=str, help="Type of s3 or s5.")
    parser.add_argument("--timestamp_file", type=str, help="The file to store the timestamp of test start.")
        
    args = parser.parse_args()
    
    # print(f"Interface: {args.interface}")
    # print(f"Target: {args.target}")
    # print(f"Delay: {args.delay}")
    # print(f"Retry: {args.retry}")
    # print(f"WakeType: {args.waketype}")
    # print(f"PowerType: {args.powertype}")
    
    delay = args.delay
    retry = args.retry
    
    ip, mac = get_ip_mac(args.interface)
    print(ip, mac)
    if ip is None: 
        print("Error: failed to get the ip address.")
        # sys.exit(1)
        
    url = f"http://{args.target}"
    req = {
          "DUT_MAC": mac,
          "DUT_IP": ip, 
          "delay": args.delay, 
          "retry_times": args.retry, 
          "wake_type": args.waketype,
          }
    # resp = post(url="http://127.0.0.1:8090/", json=req, retry=3)

    try:
        #send the request to wol server
        resp = post(url, json=req, retry=3)
        result_dict = resp.json()
        print(result_dict)
    except requests.exceptions.ConnectionError as e:
        print("***ConectionError***")
        print("Connection error:", e)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        pinrt("***HTTPError")
        print("HTTP error:", e)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        pritn("***ReqqustException error***")
        print("Request error:", e)
        sys.exit(1)
        
    if resp.status_code == 200 and result_dict["DUT_IP"] == ip:
        print("Get the answer from WOL server!")
    #bring up the system. The time should be delay*retry*2
    bring_up_system("rtc", delay*retry*2)
    
    #write the time stamp
    write_timestamp(args.timestamp_file)

    #s3 or s5 the system
    # s3_or_s5_system(args.powertype)
    
    print(resp.status_code, resp.json())    

if __name__ == "__main__":
    main()




