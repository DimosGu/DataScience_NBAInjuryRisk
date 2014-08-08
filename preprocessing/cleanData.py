"""
----------------------------------------------------------------------
    cleanData.py
----------------------------------------------------------------------
    Cleans raw data scraped from the web and stores in new csv files
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2014-08-08
----------------------------------------------------------------------
"""


import re
import numpy as np
import pandas as pd


def cleanDemographics_NBA():
    """
    Clean NBA demographics
    """
    # Read NBA demographics CSV
    demo_df = pd.read_csv('../../data/NBA_Player_Demographics__RAW.csv', parse_dates=['BirthDate'])
    # This dataframe has 'Player' sorted by first name
    # Drop rows with missing data
    demo_df = demo_df.dropna()
    # Only keep the png file name of the picture
    ##      http://i.cdn.turner.com/nba/nba/.element/img/2.0/sect/statscube/players/large/
    demo_df['PictureURL'] = demo_df['PictureURL'].map(lambda x: x.split('/')[-1])
    # Only keep the player ID for the stats URL
    ##      http://stats.nba.com/player/#!/{stats_url}/
    demo_df['StatsURL'] = demo_df['StatsURL'].map(lambda x: x.split('#!')[1][1:-1])
    # -------
    # Read NBA player link CSV
    link_df = pd.read_csv('../../data/NBA_Player_ProfileLinks__RAW.csv')
    # Only keep the target for the profile URL
    ##      http://www.nba.com/playerfile/
    link_df['ProfileURL'] = link_df['ProfileURL'].map(lambda x: x.split('playerfile/')[1])
    # This dataframe has 'Player' sorted by last name (**preferred**)
    # -------
    # Merge dataframes
    df = pd.merge(link_df, demo_df, on='Player')
    # Write CSV
    df.to_csv('../../data/NBA_Player_Demographics.csv', index=False, date_format='%Y-%m-%d')

"""----------------------------------------------------------------"""
def cleanGameLogs_BR():
    """
    Clean game log file; separate regular season
    """
    df = pd.read_csv('../../data/BR_Player_GameLogs__RAW.csv', parse_dates=['Date'])
    # Minutes played
    df['MP'].fillna('999:0', inplace=True)
    df['MP'] = df['MP'].map(lambda x: np.round(np.float(int(x.split(':')[0]) + np.float(x.split(':')[1])/60.0), decimals=2))
    df.MP[df.MP == 999] = np.nan
    # Age
    df['Age'] = df['Age'].map(lambda x: np.round(np.float(int(x.split('-')[0]) + np.float(x.split('-')[1])/365.0), decimals=3))
    # Update HomeAway to Bool
    df.insert(10, u'Home', True)
    df.Home[df.HomeAway == u'Away'] = False
    # Update WinLoss to Bool and points
    df.insert(12, u'Win', True)
    df.Win = df.WinLoss.map(lambda x: re.findall('^([WL])', x)[0])
    df.Win[df.Win == u'W'] = True
    df.Win[df.Win == u'L'] = False
    df.Win = df.Win.astype(np.bool)
    df.insert(13, u'PtDif', 0)
    df.PtDif = df.WinLoss.map(lambda x: np.int(re.findall('[+-]\d+', x)[0]))
    # Delete columns
    df = df.drop(['HomeAway', 'WinLoss', 'FG%', '3P%', 'FT%', 'GmSc', '+/-'], axis=1)
    # Separate regular season from playoffs
    reg_df = df[df.Season == u'Regular']
    reg_df = reg_df.drop('Season', axis=1)
    # Write to CSV
    reg_df.to_csv('../../data/BR_Player_GameLogs_RegularSeason.csv', index=False, date_format='%Y-%m-%d')

"""----------------------------------------------------------------"""
def cleanStatsSummary_BR(csvName):
    """
    Clean Basketball-Reference data
    """
    # Manually fill in missing Position information first
    # Read CSV
    df = pd.read_csv('../../data/' + csvName + '__RAW.csv')
    # Use convention to name season by the year it ends
    # (e.g., 2013-14 season is named 2014)
    df['Season'] = df['Season'].map(lambda x: int(x[:4])+1)
    # Fill in missing data for percentage (if null, put 0)
    _ = df.fillna({'FGpct':0, '3Ppct':0, '2Ppct':0, 'FTpct':0}, inplace=True)
    # Fill in position data
    posDict = {'PG':1, 'SG':2, 'SF':3, 'PF':4, 'C':5}
    df['Pos'] = df['Pos'].map(lambda x: posDict[str(x).split('-')[0]])
    # Get rid of league (assume NBA)
    df = df.drop('Lg', axis=1)
    # Clean up instances where player switches teams during a season;
    # Only keep the totals
    playerSeasonInd = df.ix[df['Tm'].str.contains('TOT'), ['Player','Season']]
    for indx in playerSeasonInd.index[::-1]:
        dropPlayer = playerSeasonInd.ix[indx, 'Player']
        dropSeason = playerSeasonInd.ix[indx, 'Season']
        # Check for up to three teams in one season
        for i in range(3,0,-1):
            if df.ix[indx+i, 'Player'] == dropPlayer and df.ix[indx+i, 'Season'] == dropSeason:
                df = df.drop(indx+i)
    # Drop seasons prior to 2010
    df = df[df.Season >= 2010]
    # Write CSV
    df.to_csv('../../data/' + csvName + '.csv', index=False)

"""----------------------------------------------------------------"""
def main():
    """
    Main function for running
    """
    cleanDemographics_NBA()
    cleanGameLogs_BR()
    cleanStatsSummary_BR('BR_Player_StatsSummary_RegularSeason_Total')
    cleanStatsSummary_BR('BR_Player_StatsSummary_RegularSeason_PerGame')
    getSeasonSummary_BR()


"""*******************************************************************
*                                                                    *
*                   Script Execution                                 *
*                                                                    *
*******************************************************************"""
if __name__ == '__main__':
    main()
