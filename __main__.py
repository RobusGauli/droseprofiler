import argparse
import yaml
from serverprofiler.master import Master
from serverprofiler.slave import Slave

def _start_master_process(path):
    
    with open(path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    config = {}
    config['MASTER_HOST'] = cfg['master']['host']
    config['MASTER_PORT'] = cfg['master']['port']
    config['MASTER_HTTP_PORT'] = cfg['masterhttp']['port']
    master = Master(config=config)
    master.run()

def _start_slave_process(path: str):

    with open(path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    config = {}
    config['SLAVE_ID'] = cfg['slave']['id']
    config['MASTER_PORT'] = cfg['slave']['masterport']
    config['MASTER_HOST'] = cfg['slave']['masterhost']
    slave = Slave(config=config)
    slave.run()


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
    parser.add_argument(
        '-yfp', '--yaml-file-path',
        required=True,
        dest='path',
        action='store',
        help='Yaml configuration file path.'
    )
    args = parser.parse_args()
    
    if args.is_slave:
        _start_slave_process(args.path)
    else:
        _start_master_process(args.path)
        

