#!/usr/bin/python3

import subprocess
import re
import argparse
import logging
import sys


def get_timestamp(file):
    with open(file, "r") as f:
        saved_timestamp = float(f.read())
        logging.info(f"saved_timestamp: {saved_timestamp}")
    return saved_timestamp


def extract_timestamp(log_line):
    pattern = r"(\d+\.\d+)"
    match = re.search(pattern, log_line)

    if match:
        return float(match.group(1))
    else:
        return None


def get_suspend_boot_time(type):
    # get the time stamp of the system resume from suspend for s3
    # or boot up for s5
    command = ["journalctl", "-b", "0", "--output=short-unix"]
    result = subprocess.run(command, capture_output=True, text=True)
    logs = result.stdout.splitlines()

    latest_system_back_time = None

    if type == "s3":
        for log in reversed(logs):
            if r"suspend exit" in log:
                logging.debug(log)
                latest_system_back_time = extract_timestamp(log)
                logging.info(f"suspend time: {latest_system_back_time}")
                return latest_system_back_time
    elif type == "s5":
        # the first line of system boot up
        log = logs[0]
        latest_system_back_time = extract_timestamp(log)
        logging.info(f"boot_time: {latest_system_back_time}")
        return latest_system_back_time
    else:
        sys.exit("Invalid type. Please use s3 or s5.")

    if latest_system_back_time is None:
        sys.exit("cannot find 'suspend exit' or boot time in kernel log")


def main():
    parser = argparse.ArgumentParser(
        description="Parse command line arguments.")

    parser.add_argument("--interface", required=True,
                        help="The network interface to use.")
    parser.add_argument("--powertype", type=str, help="Waked from s3 or s5.")
    parser.add_argument("--timestamp_file", type=str,
                        help="The file to store the timestamp of test start.")
    parser.add_argument("--delay", type=int, default=60,
                        help="Delay between attempts (in seconds).")
    parser.add_argument("--retry", type=int, default=3,
                        help="Number of retry attempts.")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        stream=sys.stdout,
        format="%(levelname)s: %(message)s",
    )

    logging.info("Wake on LAN log check test started.")

    interface = args.interface
    powertype = args.powertype
    timestamp_file = args.timestamp_file
    delay = args.delay
    max_retries = args.retry

    logging.info(f"Interface: {interface}")
    logging.info(f"PowerType: {powertype}")

    test_start_time = float(get_timestamp(timestamp_file))
    system_back_time = float(get_suspend_boot_time(powertype))

    time_difference = system_back_time - test_start_time

    logging.info(f"time difference: {time_difference}")

    # system_back_time - test_start_time > 1.5*max_retries*delay which meanse
    # the system was bring up by rtc other than Wake-on-lan
    expect_time_range = 1.5*max_retries*delay
    if time_difference > expect_time_range:
        sys.exit(f"Time difference is {time_difference} greater than "
                 f"1.5*delay*retry {expect_time_range}")
    elif time_difference < 0:
        sys.exit("Time difference is less than 0.")
    else:
        logging.info("Wake-on-lan workes well.")
        sys.exit(True)


if __name__ == "__main__":
    main()
