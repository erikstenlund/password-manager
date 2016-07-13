import sys
import os
import json

from getpass import getpass
from pysqlcipher3 import dbapi2 as sqlite
from dbox_filesync import DropboxSync


class UnlockedDbCursor():
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        self.conn = sqlite.connect(self.db)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA key='%s'" % getpass())
        return self.c

    def __exit__(self, type, value, tb):
        self.conn.commit()
        self.c.close()
        self.conn.close()


def new(args, flags, config):
    if '-f' not in flags and '--force' not in flags:
        conf = input(
            "Are you sure? "
            "This will remove already existing local db-files "
            "(y/N) "
        )
        if conf not in ['y', 'Y']:
            return 0

    with UnlockedDbCursor(PATH + config['db']) as cursor:
        cursor.execute(
            'CREATE TABLE passwords (identifier text, password text)'
        )


def _get_identifer(cmd, args):
    identifier_index = args.index(cmd) + 1
    if len(args) <= identifier_index:
        return '__err'
    else:
        return args[identifier_index]


def get(args, flags, config):
    identifier = _get_identifer('get', args)
    if identifier is '__err':
        print('Err: No such identifier')
        return 0

    with UnlockedDbCursor(PATH + config['db']) as cursor:
        cursor.execute(
                'SELECT password FROM passwords WHERE identifier=?',
                (identifier, )
        )
        print(cursor.fetchone()[0])


def _gen_pwd():
    # ToDo
    return 'correcthorsebatterystaple'


def generate(args, flags, config):
    identifier = _get_identifer('generate', args)

    if identifier is '__err':
        print('Err: Missing identifier')
        return 0

    pwd = _gen_pwd()

    with UnlockedDbCursor(PATH + config['db']) as cursor:
        cursor.execute(
                'INSERT INTO passwords VALUES (?, ?)',
                (identifier, pwd)
        )

def pull_db(args, flags, config):
    if 'cloud' not in config:
        print('Err: No cloud settings') 
        return 0

    if 'provider' not in config['cloud']:
        print('Err: No service provider')
        return 0

    if 'token' not in config['cloud']:
        print('Err: Token missing')
        return 0
    
    cloud = DropboxSync(config['cloud']['token'])
    print(cloud.pull(PATH + config['db'], config['db']))

def push_db(args, flags, config):
    if 'cloud' not in config:
        print('Err: No cloud settings') 
        return 0

    if 'provider' not in config['cloud']:
        print('Err: No service provider')
        return 0

    if 'token' not in config['cloud']:
        print('Err: Token missing')
        return 0
    
    cloud = DropboxSync(config['cloud']['token'])
    print(cloud.push(PATH + config['db'], config['db']))


def main():
    commands = {
        'new': new,
        'get': get,
        'generate': generate,
        'pull-db': pull_db,
        'push-db': push_db
    }

    flags = [x for x in sys.argv if x.startswith('-')]
    args = [x for x in sys.argv if x not in flags]

    if len(args) < 2:
        print('Err: Missing command')
        return 0

    command = args[1]
    if command not in commands:
        print('Err: Incorrect command')
        return 0
    
    
    config = {}
    if os.path.isfile(PATH + 'config.json'):
        with open(PATH + 'config.json') as f:
            config = json.load(f)

    if 'db' not in config:
        config['db'] = 'database.db'

    commands[command](args, flags, config)

PATH = ''
if __name__ == '__main__':
    main()
