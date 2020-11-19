import datetime
import json
import os
import sqlite3
import subprocess


_conf = {}


def init():
    '''
    initializing module:
        1. initialize and update _conf
        2. create table if not exists
        3. create datadir if not exists
    '''
    _conf['dbname'] = 'record.db' # file name of the database
    _conf['datadir'] = '.data/' # where to store computation results
    _conf['confjs'] = '~/.nedrconf' # configure file

    # update _conf if configure file exists
    if os.path.exists(_conf['confjs']):
        with open(_conf['confjs'], 'r', encoding='utf-8') as f:
            _conf.update(json.load(f))

    conn = sqlite3.connect(_conf['dbname'], detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()

    # create table Records
    cursor.execute('''
CREATE TABLE IF NOT EXISTS Records 
(recordID INTEGER PRIMARY KEY AUTOINCREMENT,
 commitID TEXT NOT NULL,
 date timestamp NOT NULL,
 calculator TEXT NOT NULL,
 datapath TEXT NOT NULL,
 description TEXT)
''')

    # check existence of datadir
    if not os.path.exists(_conf['datadir']):
        os.mkdir(_conf['datadir'])

    return
    

init()


def register(calculator, paras, *, description=None, **kw):
    '''
    insert a record to table as follows:
        1. get git commitID (Warning if git status is not clean)
        2. add column if needed
        3. construct record tuple 
        4. insert record

    return datapath of that record.
    '''
    conn = sqlite3.connect(_conf['dbname'], detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()

    commitID = _check_git_commitID()

    date = datetime.datetime.now()

    paras = _ensure_safety(paras)
    _add_columns(paras, conn)

    datapath = _generate_datapath(conn)

    cursor.execute('''
    INSERT INTO Records (commitID, date, calculator, datapath, description)
    VALUES (?,?,?,?,?)
    ''',(commitID, date, calculator, datapath, description))

    cursor.execute('SELECT MAX(recordID) FROM Records')
    recordID = cursor.fetchone()[0]

    for k, v in paras.items():
        cursor.execute('''UPDATE Records SET %s=? 
        WHERE recordID=?'''%k, (v, recordID))

    conn.commit()
    conn.close()

    return datapath, recordID


def get_datapath(recordID, remove_record=False):
    '''return datapath of recordID. 
    If remove_record is True, remove that record from database.
    Raise ValueError if record not found.

    Note: we do not delete files under that datapath.'''
    conn = sqlite3.connect(_conf['dbname'], detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()
    cursor.execute('''SELECT datapath FROM Records 
    WHERE recordID=?''', (recordID,))
    datapath = cursor.fetchone()[0]
    if datapath is None:
        raise ValueError('record not exist')
    if remove_record:
        cursor.execute('''DELETE FROM Records
        WHERE recordID=?''', (recordID,))
        conn.commit()
    conn.close()
    return datapath


def _check_git_commitID():
    '''return the last git commitID. Warning if git status is not clean.'''
    status = subprocess.run(['git', 'status', '-s'], stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
    if status:
        print('Warning: git status not clean!')
        print(status)
    commitID = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
    return commitID


def _ensure_safety(paras):
    '''prevent injection from paras' keys'''
    safe_paras = {}
    for k, v in paras.items():
        new_k = str(k).replace(' ', '')
        safe_paras[new_k] = v
    return safe_paras


def _add_columns(paras, conn):
    '''add column named with key in paras if not exists'''
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Records')
    column_names = [d[0] for d in cursor.description]

    for arg_key, arg_value in paras.items():
        if arg_key not in column_names:
            if isinstance(arg_value, int):
                dtype = 'INT'
            elif isinstance(arg_value, float):
                dtype = 'REAL'
            else:
                arg_value = str(arg_value)
                dtype = 'TEXT'

            cursor.execute('ALTER TABLE Records ADD %s %s'%(arg_key, dtype))


def _generate_datapath(conn):
    '''return a directory (create it if not exists) for storing data.'''
    cursor = conn.cursor()

    cursor.execute('SELECT MAX(recordID) FROM Records')
    n = cursor.fetchone()[0]
    n = 1 if n is None else n+1

    today = datetime.date.today()
    datapath = _conf['datadir']+'{}-{}/'.format(today, n)

    if not os.path.exists(datapath):
        print('mkdir', datapath)
        os.mkdir(datapath)

    return datapath
