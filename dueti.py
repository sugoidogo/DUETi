import logging

log=logging.getLogger(__name__)

DEFAULT_MBR_REGEX='(boot0(md)?|Mbr.com)$'
DEFAULT_PBR_REGEX='(boot1f32(alt)?|bs32.com)$'

# os.O_BINARY = nt.O_BINARY = 4
# since nt is platform-specific, we have to hard-code that value
O_BINARY = 4

def downloadHTTP(url,destination,mbr_regex=None,pbr_regex=None):
    from urllib.request import urlopen
    from io import BytesIO
    import zipfile,re

    if not mbr_regex:
        mbr_regex=DEFAULT_MBR_REGEX
    if not pbr_regex:
        pbr_regex=DEFAULT_PBR_REGEX

    log.debug('downloadHTTP('+url+','+destination+','+mbr_regex+','+pbr_regex+')')

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
            if re.search(mbr_regex,filename):
                log.info('found mbr chainloader as '+filename+' in '+dlname)
                mbr_regex=destination+'/'+dlname+'/'+filename
                extract=True
                continue
            if re.search(pbr_regex,filename):
                log.info('found pbr chainloader as '+filename+' in '+dlname)
                pbr_regex=destination+'/'+dlname+'/'+filename
                extract=True
        if extract:
            log.info('extracting '+dlname+' to '+destination)
            archive.extractall(destination+'/'+dlname)
            return mbr_regex,pbr_regex
    raise FileNotFoundError('DUET mbr/pbr not found')

def downloadDUET(source,destination,mbr_regex=None,pbr_regex=None):
    from urllib.request import urlopen
    import json

    if not mbr_regex:
        mbr_regex=DEFAULT_MBR_REGEX
    if not pbr_regex:
        pbr_regex=DEFAULT_PBR_REGEX

    log.debug('downloadDUET('+source+','+destination+','+mbr_regex+','+pbr_regex+')')

    match source:
        case 'clover':
            source='CloverHackyColor/CloverBootloader'
        case 'opencore':
            source='acidanthera/OpenCorePkg'
        # https://winraid.level1techs.com/t/guide-nvme-boot-for-systems-with-legacy-bios-and-uefi-board-duet-refind/32251
        case 'edk2015':
            args.download_source='https://drive.usercontent.google.com/download?id=1NtXFq__OYDX4uM-x3lzHDFFhjNO79m7p&export=download&authuser=0'
        case 'edk2020':
            args.download_source='https://drive.usercontent.google.com/download?id=1ogEdBzKrLRkz0SRwLphpFemRLWmgayA-&export=download&authuser=0'

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
                return downloadHTTP(asset['browser_download_url'],destination,mbr_regex,pbr_regex)
            except FileNotFoundError as e:
                log.warning(e)
                pass
    raise FileNotFoundError('DUET mbr/pbr not found')

def writembr(source,dest):
    import os

    log.info('writing '+source+' to '+dest)
    dest=os.open(dest, os.O_RDWR | O_BINARY)
    source=os.open(source, os.O_RDONLY | O_BINARY)

    buffer=os.read(source, 440)
    buffer+=os.read(dest, 512)[440:]
    os.lseek(dest, 0, os.SEEK_SET)
    os.write(dest, buffer)
    os.fsync(dest)

    os.close(source)
    os.close(dest)

def writepbr(source,dest):
    import os

    log.info('writing '+source+' to '+dest)
    dest=os.open(dest, os.O_RDWR | O_BINARY)
    source=os.open(source, os.O_RDONLY | O_BINARY)

    buffer=os.read(source, 3)
    buffer+=os.read(dest, 512)[3:90]
    os.lseek(source, 90, os.SEEK_SET)
    buffer+=os.read(source, 422)
    os.lseek(dest, 0, os.SEEK_SET)
    os.write(dest, buffer)
    os.fsync(dest)

    os.close(source)
    os.close(dest)

def main():
    import argparse
    from sys import stdout

    logging.basicConfig(stream=stdout,level=logging.INFO,format='%(message)s')

    parser=argparse.ArgumentParser(
        prog='dueti',
        description='DUET Installer'
    )

    parser.add_argument(
        '-l','--level','--log-level',
        help='logging level. One of: debug,info,warning,error,critical',
        default='info'
    )

    parser.add_argument(
        '--mbr-source',
        help='path to read mbr boot sector from'
    )

    parser.add_argument(
        '--pbr-source',
        help='path to read pbr boot sector from'
    )

    parser.add_argument(
        '--download-source',
        help='source to download DUET files from.\
            one of: opencore, clover, edk2015, edk2020,\
            or a GitHub repo in the format "author/name".\
            In this mode, --(mbr/pbr)-source can be used\
            to override the default regex for finding DUET files.'
    )

    parser.add_argument(
        '--download-dest',
        help='path to download DUET files to. Defaults to ./downloads',
        default='./downloads'
    )
    
    parser.add_argument(
        '--mbr-dest',
        help='path to write mbr boot sector to'
    )

    parser.add_argument(
        '--pbr-dest',
        help='path to write pbr boot sector to'
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

    if not (args.download_source or args.mbr_dest or args.pbr_dest):
        log.error('one of --download_source, --mbr-dest, or --pbr-dest is required')
        parser.print_help()
        exit(1)

    if args.download_source:
        args.mbr_source,args.pbr_source=downloadDUET(args.download_source,args.download_dest,args.mbr_source,args.pbr_source)

    if args.mbr_dest:
        if not args.mbr_source:
            log.error('one of --download-source or --mbr-source required with --mbr-dest')
            exit(1)
        writembr(args.mbr_source, args.mbr_dest)

    if args.pbr_dest:
        if not args.pbr_source:
            log.error('one of --download-source or --pbr-source required with --pbr-dest')
            exit(1)
        writepbr(args.pbr_source, args.pbr_dest)
    
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