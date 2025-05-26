import logging

log=logging.getLogger(__name__)

DEFAULT_MBR_REGEX='(boot0(md)?|Mbr.com|grldr.mbr)$'
DEFAULT_PBR_REGEX='(boot1f32(alt)?|bs32.com)$'
DEFAULT_COPY_REGEX='(boot(6|7|X64)|Efildr20|grldr|menu.lst|(?<!32)/EFI/|/Refind/|RefindPlus.REL.efi|Sample.plist)$'
DEFAULT_RENAME=['bootX64:boot','boot7:boot','Sample.plist:efi/oc/Sample.plist','Refind:efi/boot',
'EFI/Drivers:efi/boot/drivers','efi/boot/refind.efi:efi/boot/bootx64.efi','x64_RefindPlus_REL.efi:efi/boot/bootx64.efi']

# os.O_BINARY = nt.O_BINARY = 4
# since nt is platform-specific, we have to hard-code that value
O_BINARY = 4

def downloadHTTP(url,destination,mbr_regex=None,pbr_regex=None,copy_regex=None):
    from urllib.request import urlopen
    from io import BytesIO
    import zipfile,re

    if not mbr_regex:
        mbr_regex=DEFAULT_MBR_REGEX
    if not pbr_regex:
        pbr_regex=DEFAULT_PBR_REGEX
    if not copy_regex:
        copy_regex=DEFAULT_COPY_REGEX

    log.info('opening '+url)

    response=urlopen(url)
    dlname=response.headers['content-disposition']
    dlname=dlname.replace('attachment; filename=','')
    dlname=dlname.replace('"','')
    log.debug('got '+dlname)
    with zipfile.ZipFile(BytesIO(response.read())) as archive:
        extract=False
        mbr_source=None
        pbr_source=None
        copy_source=[]
        for filename in archive.namelist():
            #log.debug(filename)
            extracted_path=destination+'/'+dlname+'/'+filename
            if re.search(mbr_regex,filename):
                log.info('found mbr chainloader at '+filename+' in '+dlname)
                mbr_source=extracted_path
                extract=True
                continue
            if re.search(pbr_regex,filename):
                log.info('found pbr chainloader at '+filename+' in '+dlname)
                pbr_source=extracted_path
                extract=True
                continue
            if re.search(copy_regex,filename):
                log.info('found bootloader file(s) at '+filename+' in '+dlname)
                copy_source.append(extracted_path)
                extract=True
                continue
        if extract:
            log.info('extracting '+dlname+' to '+destination)
            archive.extractall(destination+'/'+dlname)
            return mbr_source,pbr_source,copy_source
    raise FileNotFoundError('DUET files not found')

def downloadDUET(source,destination,mbr_regex=None,pbr_regex=None,copy_regex=None):
    from urllib.request import urlopen
    import json

    if not mbr_regex:
        mbr_regex=DEFAULT_MBR_REGEX
    if not pbr_regex:
        pbr_regex=DEFAULT_PBR_REGEX
    if not copy_regex:
        copy_regex=DEFAULT_COPY_REGEX

    match source:
        case 'clover':
            source='CloverHackyColor/CloverBootloader'
        case 'opencore':
            source='acidanthera/OpenCorePkg'
        case 'refindplus':
            source='dakanji/RefindPlus'
        # https://winraid.level1techs.com/t/guide-nvme-boot-for-systems-with-legacy-bios-and-uefi-board-duet-refind/32251
        case 'edk2015':
            source='https://github.com/sugoidogo/DUETi/releases/download/v0/DUET_EDK2015_REFIND.zip'
        case 'edk2020':
            source='https://github.com/sugoidogo/DUETi/releases/download/v0/DUET_EDK2020_REFIND.zip'
        # https://www.insanelymac.com/forum/topic/359685-a-tip-for-anyone-who-wants-to-run-a-uefi-operating-system-on-a-bios-only-commuter/
        case 'grub4dos':
            source='https://github.com/sugoidogo/DUETi/releases/download/v0/grub4dos.zip'

    if(source.startswith('http')):
        return downloadHTTP(source,destination)
    
    log.info('searching releases from '+source)
    url='https://api.github.com/repos/'+source+'/releases'
    log.debug('opening '+url)
    response=urlopen(url)
    response=response.read()
    response=json.loads(response)
    for release in response:
        url=release['assets_url']
        log.debug('opening '+url)
        release=urlopen(url)
        release=release.read()
        release=json.loads(release)
        for asset in release:
            log.info('searching '+asset['name'])
            try:
                return downloadHTTP(asset['browser_download_url'],destination,mbr_regex,pbr_regex,copy_regex)
            except Exception as e:
                log.warning(e)
                pass
    raise FileNotFoundError('DUET files not found')

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
    getFS()
    writepbr(source,dest)

def writefat32(source,dest):
    import os

    log.debug('writefat32')
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

def writehfs(source,dest):
    import os

    log.debug('writehfs')
    log.info('writing '+source+' to '+dest)
    dest=os.open(dest, os.O_RDWR | O_BINARY)
    source=os.open(source, os.O_RDONLY | O_BINARY)

    os.write(dest,os.read(source,1024))
    os.fsync(dest)

    os.close(dest)
    os.close(source)

def writeexfat(source,dest):
    import os,struct,math

    log.debug('writeexfat')
    log.info('writing '+source+' to '+dest)
    dest=os.open(dest, os.O_RDWR | O_BINARY)
    source=os.open(source, os.O_RDONLY | O_BINARY)

    buffer=os.read(dest,512)
    buffer=buffer[:120]+os.read(source,512)[120:390]+buffer[390:]

    # https://gist.github.com/twlee79/81f1b8f62246952c2efaaf5935058ce6
    sectorSize=2**buffer[108]
    buffer+=os.read(dest,(sectorSize*11)-512)
    checksum=0
    for index,byte in enumerate(buffer):
        match index:
            case 106,107,112:
                pass
            case _:
                checksum = ((checksum << 31) | (checksum >> 1)) + byte
                checksum &= 0xFFFFFFFF
    checksum_repeats = math.ceil(sectorSize/4)
    checksum_packed = (struct.pack("<L",checksum)*checksum_repeats)[:sectorSize]

    os.write(dest,checksum_packed)
    os.lseek(source,0,os.SEEK_SET)
    os.write(dest,buffer)
    os.fsync(dest)

    os.close(dest)
    os.close(source)


def copy(sources,dest,renames=[]):
    from shutil import copy2,copytree,rmtree,move

    for source in sources:
        try:
            if source[-1]=='/':
                source=source[:-1]
            basename=source.split('/')[-1]
            copytree(source,dest+'/'+basename,dirs_exist_ok=True)
            log.info('copied '+source+' to '+dest+'/'+basename)
        except NotADirectoryError:
            copy2(source,dest+'/'+basename)
            log.info('copied '+source+' to '+dest+'/'+basename)
        except FileNotFoundError:
            log.debug('file not found, skipping move of '+source)
    
    for rename in renames:
        sourcename,destname=rename.split(':')
        try:
            copytree(dest+'/'+sourcename,dest+'/'+destname,dirs_exist_ok=True,copy_function=move)
            rmtree(dest+'/'+sourcename)
            log.info('moved '+sourcename+' to '+destname)
        except NotADirectoryError:
            move(dest+'/'+sourcename,dest+'/'+destname)
            log.info('moved '+sourcename+' to '+destname)
        except FileNotFoundError:
            log.debug('file not found, skipping rename of '+sourcename)

def getFS(device):
    import os
    global writepbr
    global DEFAULT_PBR_REGEX
    global DEFAULT_MBR_REGEX

    log.debug('checking filesystem on '+device)
    
    device=os.open(device, os.O_RDONLY | O_BINARY)
    header=os.read(device,1536)

    if 'FAT32'.encode() in header:
        log.debug('FAT32 filesystem detected - using default pbr regex and write function')
        writepbr=writefat32
        return 'FAT32'
    if 'HFS'.encode() in header:
        log.warning('HFS filesystem dected - changing default pbr regex and write function')
        writepbr=writehfs
        DEFAULT_PBR_REGEX='boot1h2?$'
        return 'HFS'
    raise Exception('Unknown filesystem. Continuing will destroy your data. Exiting')
    if 'EXFAT'.encode() in header:
        log.warning('exFAT filesystem dected - changing default pbr regex and write function')
        writepbr=writeexfat
        DEFAULT_PBR_REGEX='boot1x(alt)?$'
        return 'EXFAT'