#!usr/bin/python


"""
----------------------------------------------------------------------
    basketballROI.py
----------------------------------------------------------------------
    Flask web application
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2014-09-01
----------------------------------------------------------------------
"""


import math
import datetime
import numpy as np
from flask import Flask, render_template, request
import pymysql as mdb


# Create app instance
app = Flask(__name__)

"""----------------------------------------------------------------"""
# Homepage
@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")

"""----------------------------------------------------------------"""
# Results page
@app.route("/search.html")
def search():
    # Get player name from user input
    player_name = request.args.get("player_name", None)
    # Connect to database
    db = mdb.connect(user="root", host="localhost", db="BasketballDB", charset='utf8')
    # Query the database
    with db:
        # Cursor to database
        cur = db.cursor()
        # Demographics
        cur.execute('SELECT Height, Weight, YearsPro, BirthDate, Team, PictureURL FROM NBA_Player_Demographics WHERE Player = "%s"' % player_name)
        query_results = cur.fetchall()
        height_inches = int(query_results[0][0])
        height = str(int(math.floor(height_inches/12.0)))+"'"+str(np.mod(height_inches, 12))+'"'
        weight = str(int(query_results[0][1]))
        yearspro = str(int(query_results[0][2]))
        birthdate = (query_results[0][3]).strftime("%B %d, %Y")
        team_name = query_results[0][4]
        picture_url = query_results[0][5]
        # Team Logo
        try:
            cur.execute('SELECT ImageURL FROM NBA_Teams JOIN NBA_Player_Demographics AS Demo ON Demo.Team = CONCAT(NBA_Teams.City," ",NBA_Teams.Nickname) WHERE Demo.Player = "%s"' % player_name)
            query_results = cur.fetchall()
            logo_url = query_results[0][0]
        except:
            logo_url = None
        # Injury Risk
        cur.execute('SELECT Probability FROM Predict_InjuryRisk WHERE Player = "%s"' % player_name)
        query_results = cur.fetchall()
        probability = str(query_results[0][0])+"%"
        # Similar Players
        cur.execute('SELECT SimilarPlayers FROM Predict_SimilarPlayers WHERE Player = "%s"' % player_name)
        query_results = cur.fetchall()
        similarplayers = query_results[0][0]
    # Render template
    return render_template("search.html", player_name=player_name,
                                          picture_url=picture_url,
                                          height=height,
                                          weight=weight,
                                          yearspro=yearspro,
                                          birthdate=birthdate,
                                          team_name=team_name,
                                          logo_url=logo_url,
                                          probability=probability,
                                          similarplayers=similarplayers)

"""----------------------------------------------------------------"""
# Slides page
@app.route("/slides.html")
def slides():
    return render_template("slides.html")


"""*******************************************************************
*                                                                    *
*                   Script Execution                                 *
*                                                                    *
*******************************************************************"""
if __name__ == "__main__":
    app.run(host = '0.0.0.0')
