# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import fcntl
import os
import select
import subprocess
import time

sysfs = Path("/sys")
if (sysfs / "class/dmi/id/product_sku").read_text().strip() != "Surface_Book":
    raise SystemExit("This command is for the first-generation Surface Book.")
for name in ("BAT1", "BAT2"):
    battery = sysfs / "class/power_supply" / name
    present = battery / "present"
    if not present.is_file() or present.read_text().strip() != "1":
        raise SystemExit(f"{name} is missing.")
    if int((battery / "capacity").read_text()) <= 10:
        raise SystemExit(f"Charge {name} above 10% before detaching.")

gpu_devices = [Path("/dev/nvidia0"), Path("/dev/nvidia-uvm")]
gpu_devices.extend(Path("/dev/dri/by-path").glob("pci-0000:01:00.0-*"))
for device in gpu_devices:
    if device.exists() and subprocess.run(["/usr/bin/fuser", str(device)]).returncode == 0:
        raise SystemExit(f"The NVIDIA GPU is in use through {device}.")

matches = []
for node in (sysfs / "class/hidraw").glob("hidraw*"):
    try:
        attributes = set((node / "device/uevent").read_text().splitlines())
    except FileNotFoundError:
        continue
    if {"HID_PHYS=i2c-MSHW0030:00", "HID_ID=0018:0000045E:00000914"} <= attributes:
        matches.append(Path("/dev") / node.name)
if len(matches) != 1:
    raise SystemExit("Could not uniquely identify the Surface controller.")

report_size = 17
report_id = 0x24
def ioctl_request(number):
    return (3 << 30) | (report_size << 16) | (ord("H") << 8) | number

def read_status(fd):
    report = bytearray(report_size)
    report[0] = report_id
    count = fcntl.ioctl(fd, ioctl_request(7), report, True)
    return bytes(report[:count])

with matches[0].open("rb+", buffering=0) as controller:
    fd = controller.fileno()
    for _ in range(4):
        baseline = read_status(fd)
        if len(baseline) >= 5 and baseline[0] == report_id:
            break
        time.sleep(0.15)
    else:
        raise SystemExit("The controller did not return a valid status report.")

    print(f"Controller before release: {baseline.hex(' ')}")
    # Windows DTX maps OpenLatch to feature usage 0x86, opcode 0x09.
    release = bytearray(report_size)
    release[0] = report_id
    release[1] = 0x09
    count = fcntl.ioctl(fd, ioctl_request(6), release, True)
    print(f"Release command sent ({count} bytes). Lift the screen only if the Detach LED is green.")

    deadline = time.monotonic() + 8
    previous = baseline
    while time.monotonic() < deadline:
        readable, _, _ = select.select([fd], [], [], 0.25)
        if readable:
            report = os.read(fd, 128)
            if report and 0x20 <= report[0] <= 0x29:
                print(f"Controller input: {report.hex(' ')}")
        status = read_status(fd)
        if status and status != previous:
            print(f"Controller status changed: {status.hex(' ')}")
            previous = status
    print(f"Last controller status: {previous.hex(' ')}")
