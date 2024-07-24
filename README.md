# DUETi

Installer for DUET, a UEFI implementation for BIOS firmware

## Requirements

All you need is python and optionally a set of DUET binaries. Specifically, DUET comes in the form of an MBR boot sector, PBR boot sector, and finally the DUET binary. Since DUET doesn't include NVME, OHCI, ACPI, or PS2 support, it's married to the bootloaders you'll find it packaged with, which are responsible for loading those drivers before loading the next step in the boot chain. DUETi can also download these binaries for you if you don't have them already.

## Manual File Selection

You can find these files in the release archives of Hackintosh bootloaders like Clover and OpenCore. The MBR boot sectors (`--mbr-source`) are prefixed `boot0`, the PBR boot sectors (`--pbr-source`) are prefixed `boot1`, and the DUET binaries (`--copy-source`) are just prefixed `boot`. At the time of writing, OpenCore provides `bootIA32` and `bootX64` DUET binaries, and Clover provides `boot6` and `boot7`. You can also find builds of DUET packaged with REFIND on various forums. The MBR boot sector is named `mbr.com` and the PBR boot sector is named `bs32.com`. The DUET binary is named `Efildr20`.

## Usage

### Darwin (Mac)

```
mkdir /Volumes/efi
sudo mount -t msdos /dev/rdisk0s1 /Volumes/efi
sudo python3 dueti.py --download-source opencore --mbr-dest /dev/rdisk0 --pbr-dest /dev/rdisk0s1 --copy-dest=/Volumes/efi
```

### Linux

```
sudo python3 dueti.py --download-source clover --mbr-dest /dev/sda --pbr-dest /dev/sda1 --copy-dest=/boot/efi
```

### NT (Windows)

```
mountvol D: /S
python3 dueti.py --download-source edk2015 --mbr-dest //./PhysicalDrive0 --pbr-dest //./D: --copy-dest=D:
```
since windows has no sudo command, make sure to use an admin command prompt
## Technical Details

This script installs DUET based on the [ArchWiki installation instructions for Clover on BIOS systems](https://wiki.archlinux.org/title/Clover#BIOS_Systems), specifically implementing the following command block.

```
dd if=/dev/sda1 of=/tmp/original_PBR bs=512 count=1 conv=notrunc
cp /mnt/iso/usr/standalone/i386/boot1f32 /tmp/new_PBR
dd if=/tmp/original_PBR of=/tmp/new_PBR skip=3 seek=3 bs=1 count=87 conv=notrunc
dd if=/tmp/new_PBR of=/dev/sda1 bs=512 count=1 conv=notrunc
dd if=/mnt/iso/usr/standalone/i386/boot0ss of=/dev/sda bs=440 count=1 conv=notrunc
```

By analyzing these commands, and the contents of Clover, OpenCore, and DUET-EDK-REFIND release archives, the installation process can be described as:

1. Write first 440 bytes of `boot0*` to MBR
2. Write first 3 bytes and last 422 bytes of `boot1*` to PBR
3. Copy DUET bootloader to partition root as `boot` for hackintosh or `Efildr20` for edk