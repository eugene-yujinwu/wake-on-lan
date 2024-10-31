import subprocess
import time

def calculate_system_uptime():
    """
    计算系统启动时间与指定文件中的时间戳的时间差。

    Args:
        None

    Returns:
        float: 系统启动时间与指定文件中的时间戳的时间差（单位：秒）。
    """

    # 获取系统启动时间戳（单位：秒）
    cmd = "journalctl --output=short-unix -b 0 | head -n 1"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
    print(result)
    boot_timestamp = float(result.stdout)

    # 从文件读取预存时间戳
    with open("/tmp/log.file", "r") as f:
        saved_timestamp = float(f.read())

    # 计算时间差
    time_diff = boot_timestamp - saved_timestamp

    return time_diff

if __name__ == "__main__":
    result = calculate_system_uptime()
    print(f"系统启动时间与指定文件的时间差为：{result} 秒")