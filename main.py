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

from getpass import getpass
from dbox_filesync import DropboxSync
from pysqlcipher3 import dbapi2 as sqlite


class UnlockedDbCursor():
    def __init__(self, db, pwd=None):
        self.db = db

    def __enter__(self):
        self.conn = sqlite.connect(self.db)
        self.c = self.conn.cursor()
        if pwd is None:
            self.c.execute("PRAGMA key='%s'" % getpass())
        else:
            self.c.execute("PRAGMA key='%s'" % pwd)
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


def _get_identifier(cmd, args):
    identifier_index = args.index(cmd) + 1
    if len(args) <= identifier_index:
        return '__err'
    else:
        return args[identifier_index]


def get(args, flags, config):
    identifier = _get_identifier('get', args)
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
    identifier = _get_identifier('generate', args)

    if identifier is '__err':
        print('Err: Missing identifier')
        return 0

    pwd = _gen_pwd()

    with UnlockedDbCursor(PATH + config['db']) as cursor:
        cursor.execute(
                'INSERT INTO passwords VALUES (?, ?)',
                (identifier, pwd)
        )

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

    if '-c' in sys.argv:
        config_path = sys.argv[sys.argv.index('-c') + 1]
        sys.argv.remove(config_path)
        sys.argv.remove('-c')
    else:
        config_path = 'config.json'

    print(config_path)

    flags = [x for x in sys.argv if x.startswith('-')]
    args = [x for x in sys.argv if x not in flags]

    if len(args) < 2:
        print('Err: Missing command')
        return 0

    command = args[1]
    
    
    config = {}


    if os.path.isfile(PATH + config_path):
        with open(PATH + config_path) as f:
            config = json.load(f)

    if 'db' not in config:
        config['db'] = 'database.db'

    if command is 'new':
        new()
    elif command is 'get':
        get()
    elif command is 'generate':
        generate()

    elif command is 'pull-db' or 'push-db':
        if 'cloud' not in config:
            print('Err: No cloud settings') 
            return 0

        cloud = DropboxSync(config['cloud']['token'])
        if command is 'pull-db':
            res = pull_db(cloud, config['cloud'], config['db'])
        else:
            res = push_db()
    # Default error state
    else:
        print('Err: Incorrect command')
        return 0

    print(res)



PATH = ''
if __name__ == '__main__':
    main()
