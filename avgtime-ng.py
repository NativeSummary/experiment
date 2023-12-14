

import sqlite3

def connect_and_cursor(dbpath):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()
    return con, cur

