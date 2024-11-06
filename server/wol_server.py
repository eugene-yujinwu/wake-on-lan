#!/usr/bin/python3

from logging_utils import init_logger, get_logger
import threading
import time
import subprocess
import shlex
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
# from main import tasker_main

app = FastAPI()


@app.post("/")
async def testing(wol_request: dict):
    try:
        ret_server = tasker_main(wol_request)
        return JSONResponse(content=jsonable_encoder(ret_server),
                            status_code=200)
    except Exception as e:
        print(repr(e))

# Do initialize of logger berfore any modules be imported
# to make sure the style of logger is consistent

# TODO: switch print to logger
init_logger()

logger = get_logger(__name__)


def send_wol_command(Wol_Info: dict):
    # print("send_wol_command:", Wol_Info)

    dut_mac = Wol_Info["DUT_MAC"]
    dut_ip = Wol_Info["DUT_IP"]
    wake_type = Wol_Info["wake_type"]

    command_dict = {
                    "g": f"wakeonlan {dut_mac}",
                    "a": f"ping {dut_ip}",
                   }

    # if wake_type not in command_dict.keys:
    #     print("not a legal wake on lan type")
    #     return False
    # print(wake_type)
    # print((command_dict[wake_type]))
    try:
        # logger.debug("Executing command: {}".format(command))
        print((command_dict[wake_type]))
        output = subprocess.check_output(shlex.split(command_dict[wake_type]))
        print(output)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error occurred in tasker_main: {e}")
        return False

    except KeyError as e:
        logger.error(f"Error occurred in tasker_main: {e}")
        return False

    return True


def tasker_main(request: dict) -> dict:
    # Get the CI Service for all cids
    # data = request.get_json()
    data = request

    # TODO: try except this to avoid wol server crash
    # dut_mac = data['DUT_MAC']
    dut_ip = data['DUT_IP']
    delay = data['delay']
    # retry_times = data['retry_times']
    # wake_type = data['wake_type']

    logger.info(request)
    # logger.info(request["DUT_MAC"])
    logger.info(dut_ip)

    thread = threading.Thread(target=run_task,
                              args=(request, delay))
    thread.start()

    # add data['result'] = 'success' or data['result'] = repr(e)
    return request


def is_pingable(ip_address):
    try:
        #  use ping command to ping the host
        command = ["ping", "-c", "1", "-W", "1", ip_address]
        output = subprocess.check_output(command, stderr=subprocess.STDOUT,
                                         universal_newlines=True)
        print("ping:", output)
        return True
    except subprocess.CalledProcessError:
        # print("ping:", output)
        return False


def run_task(data, delay):

    # dut_mac = data['DUT_MAC']
    dut_ip = data['DUT_IP']
    delay = data['delay']
    retry_times = data['retry_times']
    # wake_type = data['wake_type']

    for attempt in range(retry_times):
        # logger.info("threading:", dut_mac)
        print("retry times:", attempt)
        time.sleep(delay)

        try:
            # send wol command to the dut_mac
            print("send wol command to the dut_mac")
            send_wol_command(data)
            # delay a little time, ping the DUT,
            # if not up, send wol command again

            # ping the DUT after a delay time,
            print("ping DUT to see if it had been waked up")
            time.sleep(delay)
            # ping dut
            if is_pingable(dut_ip):
                print(f"{dut_ip} is pingable, the DUT is back")
                return True
            else:
                print(f"{dut_ip} is NOT pingable, the DUT is not back, retry")

        except Exception as e:
            logger.error(f"Error occurred in tasker_main: {e}")

        # retry finished
    return False


if __name__ == "__main__":
    req = {
          "DUT_MAC": "00:00:00:00:00",
          "DUT_IP": "127.0.0.1",
          "delay": 60,
          "retry_times": 5,
          "wake_type": "g"
          }
    r1 = tasker_main(request=req)
