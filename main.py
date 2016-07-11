import sys
import sqlite3
import os

from getpass import getpass
from dbox_filesync import DropBoxSync
from pysqlcipher3 import dbapi2 as sqlite

class UnlockedDbCursor():
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        # Todo unlock db
        self.conn = sqlite.connect(self.db)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA key='%s'" % getpass())
        return self.c
    def __exit__(self, type, value, tb):
        # Todo lock db
        self.conn.commit()
        self.c.close()
        self.conn.close()

def new(args, flags):
    if '-f' not in flags and '--force' not in flags: 
        conf = input(
            "Are you sure? "
            "This will remove already existing local db-files "
            "(y/N) "
        )
        if conf not in ['y', 'Y']:
            return 0

    with UnlockedDbCursor('database.db') as cursor: 
        cursor.execute(
            'CREATE TABLE passwords (identifier text, password text)'
        )

def _get_identifer(cmd, args):
    identifier_index = args.index(cmd) + 1
    if len(args) <= identifier_index:
        return -1
    else:
        return args[identifier_index]

def get(args, flags):
    identifier = _get_identifer('get', args)
    if identifier == -1:
        print('Err missing id')
        return 0

    with UnlockedDbCursor('database.db') as cursor: 
        cursor.execute('SELECT password FROM passwords WHERE identifier=?', (identifier, ))
        print(cursor.fetchone()[0])

def _gen_pwd():
    # ToDo
    return 'correcthorsebatterystaple'

def generate(args, flags):
    identifier = _get_identifer('generate', args)


    if identifier == -1:
        print('Err missing id')
        return 0

    pwd = _gen_pwd()

    with UnlockedDbCursor('database.db') as cursor: 
        cursor.execute('INSERT INTO passwords VALUES (?, ?)', (identifier, pwd))

def pull_db(args, flags):
    if os.environ.get('CLOUD') == None:
        print('Err no cloud')
        return 0
    
    print(cloud.pull('database.db'))

def push_db(args, flags):
    if os.environ.get('CLOUD') == None:
        print('Err no cloud')
        return 0
    
    print(cloud.push('database.db'))

def main():
    commands = {
        'new' : new, 
        'get' : get, 
        'generate' : generate,
        'pull-db' : pull_db,
        'push-db' : push_db
    }

    flags = [x for x in sys.argv if x.startswith('-')]
    args = [x for x in sys.argv if x not in flags]

    command = args[1]
    if command not in commands:
        print('Err missing cmd')
        return 0
    else:
        commands[command](args, flags)

if os.environ.get('CLOUD') != None:
    cloud = DropBoxSync(os.environ.get('TOKEN'))

if __name__ == '__main__':
    main()


