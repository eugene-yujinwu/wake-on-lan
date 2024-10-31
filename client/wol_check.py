#!/usr/bin/python3

import subprocess
import re
import argparse

# timestamp_file = "/tmp/test_start_time"
# delay = 60
# max_retries = 10

def get_timestamp(file):
    with open(file, "r") as f:
        saved_timestamp = float(f.read())
        print("saved_timestamp:")
        print(saved_timestamp)
    return saved_timestamp

def extract_timestamp(log_line):
    pattern = r"(\d+\.\d+)"
    match = re.search(pattern, log_line)

    if match:
        return float(match.group(1))
    else:
        return None

def get_suspend_boot_time(type):
    command = ["journalctl", "-b", "0", "--output=short-unix"]
    result = subprocess.run(command, capture_output=True, text=True)
    logs = result.stdout.splitlines()

    latest_system_back_time = None

    if type == "s3":
        for log in reversed(logs):
            # print("log---:", log)
            if r"suspend exit" in log:
                print(log)
                latest_system_back_time = extract_timestamp(log)
                print("suspend time:", latest_system_back_time)
                # print(latest_system_back_time)
                return latest_system_back_time
    elif type == "s5":
        log = logs[0]
        latest_system_back_time = extract_timestamp(log)
        print("boot_time:", latest_system_back_time)
        return latest_system_back_time
    else:
        print("Invalid type. Please use s3 or s5.")
        return None

    # if not found "suspend exit"，return False
    if latest_system_back_time is None:
        print("cannot find 'suspend exit' or boot time in log")
        return None

def main():
    parser = argparse.ArgumentParser(description="Parse command line arguments.")

    parser.add_argument("--interface", required=True, help="The network interface to use.")
    # parser.add_argument("--waketype", default="g", help="Type of wake operation.")
    parser.add_argument("--powertype", type=str, help="Type of s3 or s5.")
    parser.add_argument("--timestamp_file", type=str, help="The file to store the timestamp of test start.")
    parser.add_argument("--delay", type=int, default=60, help="Delay between attempts (in seconds).")
    parser.add_argument("--retry", type=int, default=3, help="Number of retry attempts.")

    args = parser.parse_args()

    interface = args.interface
    # waketype = args.waketype
    powertype = args.powertype
    timestamp_file = args.timestamp_file
    delay = args.delay
    max_retries = args.retry

    print(f"Interface: {interface}")
    print(f"PowerType: {powertype}")

    test_start_time = float(get_timestamp(timestamp_file))
    system_back_time = float(get_suspend_boot_time(powertype))

    time_difference = system_back_time - test_start_time

    print("time difference:", time_difference)

    # system_back_time - test_start_time > 1.5*max_retries*delay meanse the system was
    # bring up by rtc other than Wake-on-lan
    if  time_difference > 1.5*max_retries*delay:
        print("time difference is greater than 1.5*max_retries*delay")
        return False
    elif time_difference < 0:
        print("time difference is less than 0")
        return False
    else:
        print("time difference is within the range")
        return True

if __name__ == "__main__":
    main()