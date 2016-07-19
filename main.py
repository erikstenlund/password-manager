"""
Usage:
    main.py [options] <cmd> [<identifier>]

Options:
    -c FILE
    -f, --force
    -p PASS


"""
import sys
import os
import json

from docopt import docopt
from getpass import getpass
from dbox_filesync import DropboxSync
from pysqlcipher3 import dbapi2 as sqlite


class UnlockedDbCursor():
    def __init__(self, db, pwd=None):
        self.db = db
        self.pwd = pwd

    def __enter__(self):
        self.conn = sqlite.connect(self.db)
        self.c = self.conn.cursor()
        if self.pwd is None:
            self.c.execute("PRAGMA key='%s'" % getpass())
        else:
            self.c.execute("PRAGMA key='%s'" % self.pwd)
        return self.c

    def __exit__(self, type, value, tb):
        self.conn.commit()
        self.c.close()
        self.conn.close()


def new(unlockedDbCursor, args):
    if args['--force'] == False:
        conf = input(
            "Are you sure? "
            "This will remove already existing local db-files "
            "(y/N) "
        )
        if conf not in ['y', 'Y']:
            return 0

    with unlockedDbCursor as cursor:
        cursor.execute(
            'CREATE TABLE passwords (identifier text, password text)'
        )

def get(unlockedDbCursor, args):

    if args['<identifier>'] == False:
        return 'Err: No identifier'

    with unlockedDbCursor as cursor:
        cursor.execute(
                'SELECT password FROM passwords WHERE identifier=?',
                (args['<identifier>'], )
        )
        return cursor.fetchone()[0]


def _gen_pwd():
    # ToDo
    return 'correcthorsebatterystaple'


def generate(unlockedDbCursor, args):

    if args['<identifier>'] == False:
        return 'Err: No identifier'

    pwd = _gen_pwd()
    with unlockedDbCursor as cursor:
        cursor.execute(
                'INSERT INTO passwords VALUES (?, ?)',
                (args['<identifier>'], pwd)
        )
        return cursor.fetchone()

def pull_db(cloud, cloud_config, db):
    if 'provider' not in cloud_config:
        return 'Err: No service provider'

    if 'token' not in cloud_config:
        return 'Err: Token missing'
    
    return cloud.pull(PATH + db, db)

def push_db(cloud, cloud_config, db):
    if 'provider' not in cloud_config:
        return 'Err: No service provider'

    if 'token' not in cloud_config:
        return 'Err: Token missing'
    
    return cloud.push(PATH + db, db)


def main():
    args = docopt(__doc__)

    # If not provided use default config
    if args['-c'] is None:     
       args['-c']  = 'config.json'
         
    config = {}
    if os.path.isfile(PATH + args['-c']):
        with open(PATH + args['-c']) as f:
            config = json.load(f)
    else:
        print('Err: Incorrect configuration file')
        return 0

    # Use default database if nothing else
    # is specified
    if 'db' not in config:
        config['db'] = 'database.db'

    if args['<cmd>'] in ['new', 'get', 'generate']:

        if args['-p'] is None:
            dbCursor = UnlockedDbCursor(PATH + config['db'])
        else:
            dbCursor = UnlockedDbCursor(PATH + config['db'], args['-p'])

        res = {
            'new': new,
            'get': get,
            'generate': generate
        }[args['<cmd>']](dbCursor, args)

    elif args['<cmd>'] in ['pull-db', 'push-db']:
        if 'cloud' not in config:
            print('Err: No cloud settings') 
            return 0

        cloud = DropboxSync(config['cloud']['token'])

        res = {
                'pull-db': pull_db,
                'push-db': push_db
        }[args['<cmd>']](cloud, config['cloud'], config['db'])

    # Default error state
    else:
        print('Err: Incorrect command')
        return 0

    print(res)



PATH = ''
if __name__ == '__main__':
    main()
