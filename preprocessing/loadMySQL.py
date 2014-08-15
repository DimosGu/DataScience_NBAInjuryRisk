"""
----------------------------------------------------------------------
    loadMySQL.py
----------------------------------------------------------------------
    Load csv files into MySQL database
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2014-08-15
----------------------------------------------------------------------
"""


import pandas as pd
from pandas.io import sql
import pymysql as mdb


# Open connection to MySQL database
con = mdb.connect(user="root", host="localhost", db="BasketballDB", charset="utf8")

# --------------------------------------------------------------------
def addDataframeToSQL(con, df, table_name):
    """
    Add pandas dataframe to MySQL
    """
    with con:
        # Cursor
        cur = con.cursor()
        # Execute MySQL commands:
        # Delete table if it already exists
        cur.execute("DROP TABLE IF EXISTS " + table_name)
        # Create a new dummy table
        cur.execute("CREATE TABLE " + csv_name + "(Id INT PRIMARY KEY AUTO_INCREMENT, Name VARCHAR(25))")
        # Send dataframe contents to table
        df.to_sql(con=con, name=table_name, if_exists='replace', flavor='mysql')
# --------------------------------------------------------------------

# NBA Teams
csv_name = 'NBA_Teams'
df = pd.read_csv('../../data/'+csv_name+'.csv')
df = df.set_index('City')
addDataframeToSQL(con, df, csv_name)
# NBA Player Demographics
csv_name = 'NBA_Player_Demographics'
df = pd.read_csv('../../data/'+csv_name+'.csv')
df = df.set_index('Player')
df = df.where(pd.notnull(df), None)
addDataframeToSQL(con, df, csv_name)
# Similar Players
csv_name = 'Predict_SimilarPlayers'
df = pd.read_csv('../../data/'+csv_name+'.csv')
df = df.set_index('Player')
df = df.where(pd.notnull(df), None)
addDataframeToSQL(con, df, csv_name)
# Injury Risk
csv_name = 'Predict_InjuryRisk'
df = pd.read_csv('../../data/'+csv_name+'.csv')
df = df.set_index('Player')
addDataframeToSQL(con, df, csv_name)
