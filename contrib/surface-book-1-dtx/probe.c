// SPDX-License-Identifier: GPL-2.0-or-later

#include <fcntl.h>
#include <linux/hidraw.h>
#include <linux/input.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

static int check_device(int fd)
{
	struct hidraw_devinfo info = {0};
	char phys[65] = {0};

	if (ioctl(fd, HIDIOCGRAWINFO, &info) < 0 ||
	    ioctl(fd, HIDIOCGRAWPHYS(sizeof(phys) - 1), phys) < 0) {
		perror("Identify HID device");
		return -1;
	}

	if (info.bustype != BUS_I2C || info.vendor != 0x045e ||
	    info.product != 0x0914 || strcmp(phys, "i2c-MSHW0030:00") != 0) {
		fprintf(stderr, "Expected the Surface SAM I2C HID device (MSHW0030:00, 045e:0914).\n");
		return -1;
	}

	return 0;
}

static int read_report(int fd)
{
	/* The descriptor allows four values, but firmware can return fewer. */
	unsigned char report[17] = {0x24};
	int size = ioctl(fd, HIDIOCGFEATURE(sizeof(report)), report);

	if (size < 0) {
		perror("Read feature report 0x24");
		return -1;
	}
	if (size < 5 || size > (int)sizeof(report) || (size - 1) % 4 != 0 ||
	    report[0] != 0x24) {
		fprintf(stderr, "Unexpected feature reply (%d bytes, ID 0x%02x).\n",
			size, (unsigned int)report[0]);
		return -1;
	}

	for (int i = 0; i < size; ++i)
		printf("%02x%c", (unsigned int)report[i], i + 1 == size ? '\n' : ' ');

	return 0;
}

int main(int argc, char **argv)
{
	if (argc != 2) {
		fprintf(stderr, "Usage: %s /dev/hidrawN\n", argv[0]);
		return 2;
	}

	int fd = open(argv[1], O_RDONLY | O_CLOEXEC);
	if (fd < 0) {
		perror(argv[1]);
		return 1;
	}

	int result = check_device(fd);
	if (result == 0)
		result = read_report(fd);

	close(fd);
	return result == 0 ? 0 : 1;
}
