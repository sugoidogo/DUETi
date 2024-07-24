import logging

log=logging.getLogger(__name__)

DEFAULT_REGEX_BOOT0='(boot0(md)?|Mbr.com)$'
DEFAULT_REGEX_BOOT1='(boot1f32(alt)?|bs32.com)$'
DEFAULT_DESTINATION='downloads'

# os.O_BINARY = nt.O_BINARY = 4
# since nt is platform-specific, we have to hard-code that value
O_BINARY = 4

def downloadHTTP(url,boot0=DEFAULT_REGEX_BOOT0,boot1=DEFAULT_REGEX_BOOT1,destination=DEFAULT_DESTINATION):
    from urllib.request import urlopen
    from io import BytesIO
    import zipfile,re

    log.debug('searching for '+boot0+' and '+boot1)
    log.debug('opening '+url)
    response=urlopen(url)
    dlname=response.headers['content-disposition']
    dlname=dlname.replace('attachment; filename=','')
    dlname=dlname.replace('"','')
    log.debug('got '+dlname)
    with zipfile.ZipFile(BytesIO(response.read())) as archive:
        extract=False
        namelist=archive.namelist()
        namelist.reverse()
        for filename in namelist:
            #log.debug(filename)
            if re.search(boot0,filename):
                log.info('found boot0 as '+filename+' in '+dlname)
                boot0=destination+'/'+dlname+'/'+filename
                extract=True
                continue
            if re.search(boot1,filename):
                log.info('found boot1 as '+filename+' in '+dlname)
                boot1=destination+'/'+dlname+'/'+filename
                extract=True
        if extract:
            log.info('extracting '+dlname+' to '+destination)
            archive.extractall(destination+'/'+dlname)
            return boot0,boot1
    raise FileNotFoundError('DUET mbr/pbr not found')

def downloadDUET(source,boot0=DEFAULT_REGEX_BOOT0,boot1=DEFAULT_REGEX_BOOT1,destination=DEFAULT_DESTINATION):
    from urllib.request import urlopen
    import json

    match source:
        case 'clover':
            source='CloverHackyColor/CloverBootloader'
        case 'opencore':
            source='acidanthera/OpenCorePkg'
        # https://winraid.level1techs.com/t/guide-nvme-boot-for-systems-with-legacy-bios-and-uefi-board-duet-refind/32251
        case 'edk2015':
            args.source='https://drive.usercontent.google.com/download?id=1NtXFq__OYDX4uM-x3lzHDFFhjNO79m7p&export=download&authuser=0'
        case 'edk2020':
            args.source='https://drive.usercontent.google.com/download?id=1ogEdBzKrLRkz0SRwLphpFemRLWmgayA-&export=download&authuser=0'

    if(source.startswith('http')):
        return downloadHTTP(source)
    
    log.info('getting latest release from '+source)
    url='https://api.github.com/repos/'+source+'/releases/latest'
    log.debug('opening '+url)
    response=urlopen(url)
    response=response.read()
    response=json.loads(response)
    for asset in response['assets']:
        log.debug('found '+asset['name'])
        if(asset['name'].endswith('.zip')):
            log.info('searching '+asset['name'])
            try:
                return downloadHTTP(asset['browser_download_url'],boot0,boot1,destination)
            except FileNotFoundError as e:
                log.warning(e)
                pass
    raise FileNotFoundError('DUET mbr/pbr not found')

def writembr(drive,boot0):
    import os

    log.info('writing '+boot0+' to '+drive)
    drive=os.open(drive, os.O_RDWR | O_BINARY)
    boot0=os.open(boot0, os.O_RDONLY | O_BINARY)

    buffer=os.read(boot0, 440)
    buffer+=os.read(drive, 512)[440:]
    os.lseek(drive, 0, os.SEEK_SET)
    os.write(drive, buffer)
    os.fsync(drive)

    os.close(boot0)
    os.close(drive)

def writepbr(part,boot1):
    import os

    log.info('writing '+boot1+' to '+part)
    part=os.open(part, os.O_RDWR | O_BINARY)
    boot1=os.open(boot1, os.O_RDONLY | O_BINARY)

    buffer=os.read(boot1, 3)
    buffer+=os.read(part, 512)[3:90]
    os.lseek(boot1, 90, os.SEEK_SET)
    buffer+=os.read(boot1, 422)
    os.lseek(part, 0, os.SEEK_SET)
    os.write(part, buffer)
    os.fsync(part)

    os.close(boot1)
    os.close(part)

def main():
    import argparse
    from sys import stdout

    logging.basicConfig(stream=stdout,level=logging.INFO,format='%(message)s')

    parser=argparse.ArgumentParser(
        prog='dueti',
        description='DUET Installer'
    )

    parser.add_argument(
        '-l','--level',
        help='logging level. One of: debug,info,warning,error,critical',
        default='info'
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

    download=subparsers.add_parser(
        'download',
        description='Download DUET files from GitHub'
    )
    download.add_argument(
        '-s',
        '--source',
        help='author/name of a GitHub repository,\
            or one of: clover,opencore,edk2015,edk2020',
        default='clover'
    )
    download.add_argument(
        '-d',
        '--destination',
        help='path to extract archives to',
        default=DEFAULT_DESTINATION
    )
    download.add_argument(
        '-0',
        '--boot0',
        help='regex for boot0 file to auto-select',
        default=DEFAULT_REGEX_BOOT0
    )
    download.add_argument(
        '-1',
        '--boot1',
        help='regex for boot1 file to auto-select',
        default=DEFAULT_REGEX_BOOT1
    )
    download.add_argument(
        '--drive',
        '-m',
        '--mbr',
        help='path to destination drive',
    )
    download.add_argument(
        '--partition',
        '-p',
        '--pbr',
        help='path to destination partition',
    )

    args=parser.parse_args()

    match args.level.lower():
        case 'debug':
            log.setLevel(logging.DEBUG)
        case 'info':
            log.setLevel(logging.INFO)
        case 'warning':
            log.setLevel(logging.WARNING)
        case 'error':
            log.setLevel(logging.ERROR)
        case 'critical':
            log.setLevel(logging.CRITICAL)

    log.debug('log level = '+args.level.lower())

    if args.source:
        args.boot0,args.boot1=downloadDUET(args.source,args.boot0,args.boot1,args.destination)

    if args.drive:
        writembr(args.drive, args.boot0)

    if args.partition:
        writepbr(args.partition, args.boot1)
    
    log.info('done')

if __name__ == '__main__':
    import traceback

    try:
        main()
    except Exception as e:
        trace=traceback.format_exception(e)
        exception=trace.pop()
        log.critical(exception)
        log.debug('\n'.join(trace))
        exit(1)