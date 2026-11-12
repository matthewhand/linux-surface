# Surface Book 1 detachment probe

The first-generation Surface Book uses a HID-over-I2C controller. Microsoft's
Surface DTX driver for `ACPI\MSHW0041` accesses the controller's vendor HID
collection, usage page `0xff04`, usage `0x50`. The controller on the Surface
Book 1 identifies as `MSHW0030:00` and `045e:0914`. [Microsoft driver catalog](https://www.catalog.update.microsoft.com/ScopedViewInline.aspx?updateid=b9eda916-5dce-4aae-a52c-09edce83952c)

This probe reads feature report `0x24` and prints its raw bytes. The report
descriptor declares four 32-bit fields at usages `0x86` through `0x89`. The
Windows driver's feature-read path selects this report through usage `0x86`.
The field meanings and their relationship to the latch still need hardware
validation. The probe opens the device read-only and uses GET_FEATURE.

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
