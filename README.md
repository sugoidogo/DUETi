# DUETi

Installer for DUET, a UEFI implementation for BIOS firmware

## Requirements

All you need is python and a set of DUET binaries. Specifically, DUET comes in the form of an MBR boot sector, PBR boot sector, and finally the DUET binary, which is not installed by this program, but rather just copied onto the partition with a specific name. Since DUET doesn't include NVME, OHCI, ACPI, or PS2 support, it's married to the bootloaders you'll find it packaged with, which are responsible for loading those drivers before loading the next step in the boot chain.

You can find these files in the release archives of Hackintosh bootloaders like Clover and OpenCore. The MBR boot sectors are prefixed `boot0`, the PBR boot sectors are prefixed `boot1`, and the DUET binaries are just prefixed `boot`. At the time of writing, OpenCore provides `bootIA32` and `bootX64` DUET binaries, and Clover provides `boot6` and `boot7`. The DUET binaries have to be copied to the root of the drive and renamed to `boot`. Hackintosh DUET builds require GPT partition tables, and the DUET binary must be renamed `boot`. You can then copy the EFI folder to the drive root (opencore users will find it in the IA32/X64 folders) and begin configuration of your bootloader.

You can also find builds of DUET packaged with REFIND on various forums. The MBR boot sector is named `mbr.com` and the PBR boot sector is named `bs32.com`. The DUET binary is prefixed `efildr` and keeps its name when copied onto the partition. These builds require a DOS/MBR partition table. The `Refind` folder has to be copied and renamed to `efi/boot` and the `refind.efi` file within has to be renamed to `bootx64.efi`.

## Download Mode

DUETi can now also download the bootloader files for you from GitHub releases for hackintosh bootloaders or from edk builds provided on winraid forums. By default, the Clover bootloader is downloaded to the working directory and a fat32 efi partition is assumed. You can optionally provide the drive paths to perform the download and install all in one step, after which you can copy the files needed from the download folder.

## Usage

### Darwin (Mac)

```
python3 dueti.py --mbr-source boot0 --mbr-dest /dev/rdisk1 --pbr-source boot1f32 --pbr-dest /dev/rdisk1s1
python3 dueti.py --download-source opencore --mbr-dest /dev/rdisk1 --pbr-dest /dev/rdisk1s1
```

### Linux

```
python3 dueti.py --mbr-source boot0md --mbr-dest /dev/sdb --pbr-source boot1f32alt --pbr-dest /dev/sdb1
python3 dueti.py --download-source clover --mbr-dest /dev/sdb --pbr-dest /dev/sdb1
```

### NT (Windows)

```
python3 dueti.py --mbr-source mbr.com --mbr-dest //./PhysicalDrive1 --pbr-source bs32.com --pbr-dest //./D:
python3 dueti.py --download-source edk2015 --mbr-dest //./PhysicalDrive1 --pbr-dest //./D:
```

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
3. Copy DUET bootloader to partition root as `boot` for hackintosh or `EfiLdr20` for edk

In my testing, the simple code in this script successfully installs any build of DUET on both GPT and DOS partition tables, although the appropriate partition table must still be used for the given DUET build.