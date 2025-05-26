#!/usr/bin/env python3
# nuitka-project: --onefile
# nuitka-project: --output-dir=bin/cli
# nuitka-project-if: {OS} == "Windows":
#   nuitka-project: --windows-icon-from-ico=biochip.png
#   nuitka-project: --windows-uac-admin

from dueti import *

def main():
    import argparse
    from sys import stdout
    import traceback

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
        help='path to read mbr boot sector from, or search regex when using --download-source'
    )

    parser.add_argument(
        '--pbr-source',
        help='path to read pbr boot sector from, or search regex when using --download-source'
    )

    parser.add_argument(
        '--copy-source',
        help='path to copy bootloader file(s) from, or search regex when using --download-source'
    )

    parser.add_argument(
        '--download-source',
        help='source to download DUET files from.\
            one of: opencore, clover, edk2015, edk2020,\
            or a GitHub repo in the format "author/name".'
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

    parser.add_argument(
        '--copy-dest',
        help='path to copy bootloader file(s) to'
    )

    parser.add_argument(
        '--rename',
        help='rename a copied file at the destination',
        metavar='OLDNAME:NEWNAME',
        action='extend'
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

    if args.pbr_dest:
        log.debug('FS='+getFS(args.pbr_dest))

    if args.download_source:
        args.mbr_source,args.pbr_source,args.copy_source=downloadDUET(args.download_source,args.download_dest,args.mbr_source,args.pbr_source)

    if args.mbr_dest:
        if not args.mbr_source:
            if args.download_source:
                log.error('mbr source not found in archive - exiting')
            else:
                log.error('one of --download-source or --mbr-source required with --mbr-dest')
            exit(1)
        writembr(args.mbr_source, args.mbr_dest)

    if args.pbr_dest:
        if not args.pbr_source:
            if args.download_source:
                log.error('pbr source not found in archive - exiting')
            else:
                log.error('one of --download-source or --pbr-source required with --pbr-dest')
            exit(1)
        writepbr(args.pbr_source, args.pbr_dest)

    if args.copy_dest and len(args.copy_source) != 0:
        if not args.rename:
            args.rename=DEFAULT_RENAME
        copy(args.copy_source,args.copy_dest,args.rename)
    
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