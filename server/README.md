## A daemon to recerive the request from DUT and send a wake-on-lan command to DUT to test the wake-on-lan function

The server get the request from DUT, which include the info as this: {"DUT_MAC": "00:00:00:00:00", "DUT_IP": "127.0.0.1", "delay": 60, "retry_times": 5, "wake_type": "g"}. The server will send a wake-on-lan command to the DUT with the DUT_MAC to wake up the DUT. 
