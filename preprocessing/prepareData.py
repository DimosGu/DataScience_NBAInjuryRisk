"""
----------------------------------------------------------------------
    prepareData.py
----------------------------------------------------------------------
    Prepare data for model implementation
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2014-08-08
----------------------------------------------------------------------
"""


import re
import numpy as np
import pandas as pd
from sklearn.cross_validation import train_test_split

def getSeasonSummary_BR():
    """
    Separate by year, calculate number of games missed
    """
    # Read CSV to get column names
    csvFile = open('../../data/BR_Player_StatsSummary_RegularSeason_PerGame.csv')
    csvList = csvFile.readlines()
    csvFile.close()
    # Update header to regular season and playoffs
    header = csvList[0].strip().split(',')
    pgHeader = header[0:7] + ['PerGame' + col for col in header[7:]]
    totHeader = header[0:7] + ['Tot' + col for col in header[7:]]
    # Demographics
    df_demo = pd.read_csv('../../data/BR_Player_Demographics__RAW.csv', parse_dates=['BirthDate'])
    df_demo = df_demo.drop(['URL','FromYear','ToYear','Position','BirthDate'], axis=1)
    # Open game log file
    df_gl = pd.read_csv('../../data/BR_Player_GameLogs_RegularSeason.csv', parse_dates=['Date'])
    # Read 'Per Game' season summary file
    df_pg = pd.read_csv('../../data/BR_Player_StatsSummary_RegularSeason_PerGame.csv', skiprows=1, names=pgHeader)
    # Read 'Total' season summary file
    df_tot = pd.read_csv('../../data/BR_Player_StatsSummary_RegularSeason_Total.csv', skiprows=1, names=totHeader)
    # -----------
    # 2014
    # Calculate number of inactive games
    df2014_sum = df_gl[df_gl.Year == 2014]
    df2014_sum = df2014_sum.groupby(['Player','Year'])['Inactive','DidNotPlay'].sum()
    df2014_sum = df2014_sum.reset_index()
    df2014_sum = df2014_sum.drop(['Year','DidNotPlay'], axis=1)
    df2014_sum = df2014_sum.rename(columns = {'Inactive':'GamesMissed_2014'})
    # Total
    df2014_tot = df_tot[df_tot.Season == 2014]
    df2014_tot = df2014_tot.drop('Season' , axis=1)
    # Per Game
    df2014_pg = df_pg[df_pg.Season == 2014]
    df2014_pg = df2014_pg.drop(['Season','Age','Tm','Pos','G','GS'], axis=1)
    # Merge dataframes
    df2014_merge = pd.merge(df_demo, df2014_tot, on='Player', how='inner')
    df2014_merge = pd.merge(df2014_merge, df2014_pg, on='Player', how='inner')
    df2014_merge = pd.merge(df2014_merge, df2014_sum, on='Player', how='inner')
    # Only consider players who average more than 15 minutes
    df2014_merge = df2014_merge[df2014_merge.PerGameMP >= 15]
    # Clean up random duplicates
    df2014 = df2014_merge[~df2014_merge.duplicated(subset='Player')]
    # Rename columns
    df2014_write = df2014.rename(columns = {'GamesMissed_2014':'GamesMissedCur'})
    # Save to CSV
    df2014_write.to_csv('../../data/BR_Player_Summary_RegularSeason_2014.csv', index=False)
    # ----------------------------------------------------------------
    def getYearDS(year, df_gl, df_pg, df_tot, df_demo):
        """
        Calculate previous year files based on assumptions:
         - Games not played were games missed due to injury
           - 2014, 2013, 2011, 2010 -- subtract from 82 regular season games
           - 2012 -- subtract from 66 regular season games (lockout season)
         - (prior to 2013-14 season, don't have distinction between
            Did Not Play, Inactive, Suspended)
         - Only keep for players averaging more than 15 minutes
        """
        dfyear_sum = df_gl[df_gl.Year == year]
        dfyear_sum = dfyear_sum.groupby(['Player','Year'])['G','GS'].count()
        dfyear_sum = dfyear_sum.reset_index()
        dfyear_sum = dfyear_sum.drop(['Year','GS'], axis=1)
        if year != 2012:
            dfyear_sum['GamesMissed_'+str(year)] = 82 - dfyear_sum['G']
        else:
            dfyear_sum['GamesMissed_'+str(year)] = 66 - dfyear_sum['G']
        dfyear_sum = dfyear_sum.drop('G', axis=1)
        dfyear_pg = df_pg[df_pg.Season == year]
        dfyear_pg = dfyear_pg.drop(['Season','Age','Tm','Pos','G','GS'], axis=1)
        dfyear_tot = df_tot[df_tot.Season == year]
        dfyear_tot = dfyear_tot.drop('Season', axis=1)
        df_merge = pd.merge(df_demo, dfyear_tot, on='Player', how='inner')
        df_merge = pd.merge(df_merge, dfyear_pg, on='Player', how='inner')
        df_merge = pd.merge(df_merge, dfyear_sum, on='Player', how='inner')
        df_merge = df_merge[df_merge.PerGameMP >= 15]
        df_dedup = df_merge[~df_merge.duplicated(subset='Player')]
        return df_dedup
    # ----------------------------------------------------------------
    # 2013
    df2013 = getYearDS(2013, df_gl, df_pg, df_tot, df_demo)
    df2013_write = pd.merge(df2013, df2014[['Player','GamesMissed_2014']], on='Player')
    df2013_write = df2013_write.rename(columns = {'GamesMissed_2013':'GamesMissedCur', 'GamesMissed_2014':'GamesMissedNext'})
    df2013_write.to_csv('../../data/BR_Player_Summary_RegularSeason_2013.csv', index=False)
    # 2012
    df2012 = getYearDS(2012, df_gl, df_pg, df_tot, df_demo)
    df2012_write = pd.merge(df2012, df2013[['Player','GamesMissed_2013']], on='Player')
    df2012_write = df2012_write.rename(columns = {'GamesMissed_2012':'GamesMissedCur', 'GamesMissed_2013':'GamesMissedNext'})
    df2012_write.to_csv('../../data/BR_Player_Summary_RegularSeason_2012.csv', index=False)
    # 2011
    df2011 = getYearDS(2011, df_gl, df_pg, df_tot, df_demo)
    df2011_write = pd.merge(df2011, df2012[['Player','GamesMissed_2012']], on='Player')
    df2011_write = df2011_write.rename(columns = {'GamesMissed_2011':'GamesMissedCur', 'GamesMissed_2012':'GamesMissedNext'})
    df2011_write.to_csv('../../data/BR_Player_Summary_RegularSeason_2011.csv', index=False)
    # 2010
    df2010 = getYearDS(2010, df_gl, df_pg, df_tot, df_demo)
    df2010_write = pd.merge(df2010, df2011[['Player','GamesMissed_2011']], on='Player')
    df2010_write = df2010_write.rename(columns = {'GamesMissed_2010':'GamesMissedCur', 'GamesMissed_2011':'GamesMissedNext'})
    df2010_write.to_csv('../../data/BR_Player_Summary_RegularSeason_2010.csv', index=False)

"""----------------------------------------------------------------"""
def getClassificationData():
    """
    Prepare data for classification algorithm
    """
    def getYearDF(year):
        """
        Update individual season dataframes
        """
        # Raw data
        df_in = pd.read_csv('../../data/BR_Player_Summary_RegularSeason_'+year+'.csv')
        colNames = df_in.columns.values.tolist()
        # Convert GamesMissed into binary classification - 10% of regular season
        df_in.insert(0, u'MissedBin', 0)
        df_in.MissedBin[df_in.GamesMissedNext >= 8] = 1
        # Basic data to keep
        basicCols = ['Player','MissedBin','Height','Weight','Age','G','GS']
        # Disregard percentage-based columns (redundant)
        otherCols = [colName for colName in colNames if re.match('^(PerGame|Tot).*[^pct]$', colName)]
        df = df_in.ix[:, (basicCols + otherCols)]
        # Rename columns
        df = df.rename(columns = {'G':'GamesPlayed','GS':'GamesStarted'})
        # Add season as column
        df.insert(1, u'Season', int(year))
        # Return
        return df
    # --------------
    # Get seasons prior to 2013-14 season
    df2013 = getYearDF('2013')
    df2012 = getYearDF('2012')
    df2011 = getYearDF('2011')
    df2010 = getYearDF('2010')
    # Concatenate
    buildmodel = pd.concat([df2013, df2012, df2011, df2010])
    # Write to CSV
    buildmodel.to_csv('../../data/BR_Player_Summary_BuildModel.csv', index=False)
    # ----------------------------------
    # Split into train/test (80/20) sets
    train, test = train_test_split(buildmodel, test_size=0.2, random_state=42)
    # Convert to dataframe
    train_df = pd.DataFrame(train, columns=buildmodel.columns)
    test_df = pd.DataFrame(test, columns=buildmodel.columns)
    # Write to CSV
    train_df.to_csv('../../data/BR_Player_Summary_BuildModel_Train.csv', index=False)
    test_df.to_csv('../../data/BR_Player_Summary_BuildModel_Test.csv', index=False)
    # ----------------------------------
    # Prepare for prediction
    df_in = pd.read_csv('../../data/BR_Player_Summary_RegularSeason_2014.csv')
    colNames = df_in.columns.values.tolist()
    # Basic data to keep
    basicCols = ['Player','Height','Weight','Age','G','GS']
    # Disregard percentage-based columns (redundant)
    otherCols = [colName for colName in colNames if re.match('^(PerGame|Tot).*[^pct]$', colName)]
    predict = df_in.ix[:, (basicCols + otherCols)]
    # Rename columns
    predict = predict.rename(columns = {'G':'GamesPlayed','GS':'GamesStarted'})
    # Add season as column
    predict.insert(1, u'Season', 2014)
    # Write to CSV
    predict.to_csv('../../data/BR_Player_Summary_Predict.csv', index=False)

"""----------------------------------------------------------------"""
def main():
    """
    Main function for running
    """
    getSeasonSummary_BR()
    getClassificationData()


"""*******************************************************************
*                                                                    *
*                   Script Execution                                 *
*                                                                    *
*******************************************************************"""
if __name__ == '__main__':
    main()
