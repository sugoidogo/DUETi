# DUETI

Installer for DUET, a UEFI implementation for BIOS firmware

## Requirements

All you need is python and a set of DUET binaries. Both Clover and OpenCore include them in their release archives. The MBR file will always begin with `boot0` and the PBR file will always begin with `boot1`.

## Usage

### Darwin (Mac)

```
python3 dueti.py mbr boot0ss /dev/rdisk0
python3 dueti.py pbr boot1f32alt /dev/rdisk0s1
```

### Linux

```
python3 dueti.py mbr boot0ss /dev/sda
python3 dueti.py pbr boot1f32alt /dev/sda1
```

### NT (Windows)

```
python3 dueti.py mbr boot0ss //./PhysicalDrive1
python3 dueti.py pbr boot1f32alt //./D:
```



## Overview

This script installs DUET based on the [ArchWiki installation instructions for Clover on BIOS systems](https://wiki.archlinux.org/title/Clover#BIOS_Systems)

```
dd if=/dev/sda1 of=/tmp/original_PBR bs=512 count=1 conv=notrunc
cp /mnt/iso/usr/standalone/i386/boot1f32 /tmp/new_PBR
dd if=/tmp/original_PBR of=/tmp/new_PBR skip=3 seek=3 bs=1 count=87 conv=notrunc
dd if=/tmp/new_PBR of=/dev/sda1 bs=512 count=1 conv=notrunc
dd if=/mnt/iso/usr/standalone/i386/boot0ss of=/dev/sda bs=440 count=1 conv=notrunc
```

By analyzing these commands, and the contents of both Clover and OpenCore release archives, the installation process can be described as:

1. Write first 440 bytes of `boot0*` to MBR
2. Write first 3 bytes and last 422 bytes of `boot1*` to PBR
3. Copy DUET bootloader to partition root as `boot`

This script performs steps 1 and 2. Don't forgot to copy your bootloader over as well ( `boot6` or `boot7` for Clover, `bootx64` or `bootia32` for OpenCore ).