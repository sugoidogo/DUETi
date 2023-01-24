import os

def writembr(drive,boot0):
    drive=os.open(drive, os.O_RDWR | os.O_BINARY)
    boot0=os.open(boot0, os.O_RDONLY | os.O_BINARY)

    buffer=os.read(boot0, 440)
    buffer+=os.read(drive, 512)[440:]
    os.lseek(drive, 0, os.SEEK_SET)
    os.write(drive, buffer)
    os.fsync(drive)

    os.close(boot0)
    os.close(drive)

def writepbr(part,boot1):
    part=os.open(part, os.O_RDWR | os.O_BINARY)
    boot1=os.open(boot1, os.O_RDONLY | os.O_BINARY)

    buffer=os.read(boot1, 3)
    buffer+=os.read(part, 512)[3:90]
    os.lseek(boot1, 90, os.SEEK_SET)
    buffer+=os.read(boot1, 422)
    os.lseek(part, 0, os.SEEK_SET)
    os.write(part, buffer)
    os.fsync(part)

    os.close(boot1)
    os.close(part)

if __name__ == '__main__':
    import argparse
        
    parser=argparse.ArgumentParser(
        prog='dueti',
        description='DUET Installer'
    )
    subparsers=parser.add_subparsers(required=True)

    mbr=subparsers.add_parser(
        'mbr',
        description='Install MBR chainloader',
        epilog='Examples of drive paths:\
            Windows: //./PhysicalDrive0\
            Linux: /dev/sda\
            Darwin: /dev/rdisk0'
    )
    mbr.add_argument(
        'boot0',
        help='path to a DUET MBR boot sector'
    )
    mbr.add_argument(
        'drive',
        help='path to destination device'
    )

    pbr=subparsers.add_parser(
        'pbr',
        description='Install PBR chainloader',
        epilog='Examples of partition paths:\
            Windows: //./C:\
            Linux: /dev/sda1\
            Darwin: /dev/rdisk0s1'
    )
    pbr.add_argument(
        'boot1',
        help='path to a DUET PBR boot sector'
    )
    pbr.add_argument(
        'partition',
        help='path to destination partition'
    )

    args=parser.parse_args()

    if 'boot0' in args:
        writembr(args.drive, args.boot0)

    if 'boot1' in args:
        writepbr(args.partition, args.boot1)