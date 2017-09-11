import argparse

from serverprofiler import (
    Master,
    Slave
)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Server Profiler'
    )
    parser.add_argument(
        '-s', '--slave',
        default=False,
        dest='is_slave',
        action='store_true',
        help='Enable slave mode'
    )
    args = parser.parse_args()
    
    if args.is_slave:
        s = Slave.from_cli()
        s.run()
    else:
        master = Master()
        master.run()
        

