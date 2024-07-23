import os,json,zipfile,re,logging
from urllib.request import urlopen
from urllib.error import HTTPError
from io import BytesIO
from sys import stderr,stdout

log=logging.getLogger(__name__)

def downloadDUET(url):
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
            if re.search(args.boot0,filename):
                log.info('found boot0 as '+filename+' in '+dlname)
                args.boot0=args.destination+'/'+dlname+'/'+filename
                extract=True
                continue
            if re.search(args.boot1,filename):
                log.info('found boot1 as '+filename+' in '+dlname)
                args.boot1=args.destination+'/'+dlname+'/'+filename
                extract=True
        if extract:
            log.info('extracting '+dlname+' to '+args.destination)
            archive.extractall(args.destination+'/'+dlname)
            return True
    log.error('DUET not found')
    return False

def downloadGitHub(source):
    match source:
        case 'clover':
            source='CloverHackyColor/CloverBootloader'
        case 'opencore':
            source='acidanthera/OpenCorePkg'

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
            if(downloadDUET(asset['browser_download_url'])):
                return True
    log.error('no matching files found in release archives')
    return False

def writembr(drive,boot0):
    log.info('writing '+boot0+' to '+args.drive)
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
    log.info('writing '+boot1+' to '+args.partition)
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
        default='downloads'
    )
    download.add_argument(
        '-0',
        '--boot0',
        help='regex for boot0 file to auto-select',
        default='(boot0(md)?|Mbr.com)$'
    )
    download.add_argument(
        '-1',
        '--boot1',
        help='regex for boot1 file to auto-select',
        default='(boot1f32(alt)?|bs32.com)$'
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

    if args.source:
        # https://winraid.level1techs.com/t/guide-nvme-boot-for-systems-with-legacy-bios-and-uefi-board-duet-refind/32251
        match args.source:
            case 'edk2015':
                args.source='https://drive.usercontent.google.com/download?id=1NtXFq__OYDX4uM-x3lzHDFFhjNO79m7p&export=download&authuser=0'
            case 'edk2020':
                args.source='https://drive.usercontent.google.com/download?id=1ogEdBzKrLRkz0SRwLphpFemRLWmgayA-&export=download&authuser=0'
        try:
            if args.source.startswith('http'):
                if not downloadDUET(args.source):
                    exit(1)
            else:
                if not downloadGitHub(args.source):
                    exit(1)
        except HTTPError as error:
            log.info(error,file=stderr)
            exit(1)

    if args.drive:
        writembr(args.drive, args.boot0)

    if args.partition:
        writepbr(args.partition, args.boot1)
    
    log.info('done')