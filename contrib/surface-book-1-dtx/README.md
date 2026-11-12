# Surface Book 1 latch release

The first-generation Surface Book uses a HID-over-I2C controller. Microsoft's
Surface DTX driver for `ACPI\MSHW0041` accesses the controller's vendor HID
collection, usage page `0xff04`, usage `0x50`. The controller on the Surface
Book 1 identifies as `MSHW0030:00` and `045e:0914`. [Microsoft driver catalog](https://www.catalog.update.microsoft.com/ScopedViewInline.aspx?updateid=b9eda916-5dce-4aae-a52c-09edce83952c)

## Release the latch from Linux

From this directory, run the release helper while the base is attached.

```sh
sudo /usr/bin/python3 -I release.py
```

The helper checks both battery levels, looks for processes using the NVIDIA
device, and identifies the controller before sending the release command once.
Lift the screen when the Detach LED turns green.

The release uses feature report `0x24`, usage `0x86`, with opcode `0x09`.
The command was tested on a first-generation Surface Book. The controller
reported both latches open and Linux subsequently lost the base battery and
keyboard. Support for triggering the release from the physical key remains
under investigation.

## Read controller status

The read-only probe reads feature report `0x24` and prints its raw bytes. The report
descriptor declares four 32-bit fields at usages `0x86` through `0x89`. A
Surface Book 1 returned only the first 32-bit field after the report ID.
The Windows driver's feature-read path selects this report through usage
`0x86`. The probe opens the device read-only and uses GET_FEATURE.

Build from this directory with a C compiler and Linux userspace headers.

```sh
cc -O2 -Wall -Wextra -Werror -o sb1-dtx-probe probe.c
```

Find the matching device node. Its number can change after a reboot.

```sh
for device in /sys/class/hidraw/hidraw*; do
    if grep -qx 'HID_PHYS=i2c-MSHW0030:00' "$device/device/uevent"; then
        printf '/dev/%s\n' "${device##*/}"
    fi
done
```

Run the probe with the printed device path. Root is normally needed to open
the HID device.

```sh
sudo ./sb1-dtx-probe /dev/hidrawN
```
