"""
----------------------------------------------------------------------
    makePredictions.py
----------------------------------------------------------------------
    Build classification and clustering models to identify injury
    risk and similar players; save results to csv files
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2014-08-13
----------------------------------------------------------------------
"""


import numpy as np
import pandas as pd
from sklearn.preprocessing import scale
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import RFECV
from sklearn.cross_validation import StratifiedKFold


def classifyData():
    """
    Logistic regression model to predicty injury risk
    """
    # ----------------------------------
    def prepareModel(csvname):
        # Read CSV
        data = pd.read_csv('../../data/'+csvname+'.csv')
        # Prepare for model
        X = data.drop(['Player','Season','MissedBin'], axis=1)
        y = data['MissedBin'].get_values()
        return X, y
    # ----------------------------------
    # All data
    X, y = prepareModel('BR_Player_Summary_BuildModel')
    # Training data
    X_train, y_train = prepareModel('BR_Player_Summary_BuildModel_Train')
    # Test data
    X_test, y_test = prepareModel('BR_Player_Summary_BuildModel_Test')
    # Build Logistic Regression model
    logreg = LogisticRegression()
    # Eliminate features
    skf = StratifiedKFold(y, n_folds=10)
    rfecv = RFECV(estimator=logreg, step=1, cv=skf, scoring='accuracy')
    rfecv.fit(X, y)
    # ----------------------------------
    # Train model
    X_train = X_train.ix[:, rfecv.support_]
    trainfit = logreg.fit(X_train, y_train)
    # # trainfit.score(X_train, y_train)
    # Test model
    X_test = X_test.ix[:, rfecv.support_]
    # # trainfit.score(X_test, y_test)
    # ----------------------------------
    # Fit model to whole dataset
    X = X.ix[:, rfecv.support_]
    modelfit = logreg.fit(X, y)
    # # modelfit.score(X, y)
    # ----------------------------------
    # Predict from model
    data = pd.read_csv('../../data/BR_Player_Summary_Predict.csv')
    X_predict = data.drop(['Player','Season'], axis=1)
    X_predict = X_predict.ix[:, rfecv.support_]
    # Predict probabilities
    y_predict = modelfit.predict_proba(X_predict)
    y_predict_1 = np.round(y_predict[:,1]*100)
    # New dataframe
    df = pd.DataFrame({'Player':data.Player, 'Probability':y_predict_1})
    # Write to CSV
    df.to_csv('../../data/Predict_InjuryRisk.csv', index=False)

"""----------------------------------------------------------------"""
def clusterData():
    """
    K-Means clustering model to identify similar players
    """
    # Read CSV
    df_in = pd.read_csv('../../data/NBA_Player_SportVU_RegularSeason_2014.csv')
    # Convert percentages from strings to floats
    colNames = df_in.columns.values.tolist()
    for col in colNames:
       if 'ercent' in col:
           df_in[col] = df_in[col].map(lambda x: float(x[:-1])/100)
    # Pull out subset of columns
    df_set = df_in[['Games_Played','Minutes_Per_Game',
                    'Distance_Traveled_Per_Game_MILES',
                    'Touches_Per_Game','Points_Per_Game',
                    'Assists_Per_Game','Passes_Per_Game',
                    'Steals_Per_Game','Blocks_Per_Game',
                    'Rebounds_Per_Game','Rebound_Chances_Per_Game',
                    'Drives_Per_Game','Drive_Points_Per_Game',
                    'Catch_and_Shoot_Points_Per_Game',
                    'Pull_Up_Shots_Points_Per_Game',
                    'Close_Shots_Points_Per_Game',
                    'Effective_Field_Goal_Percentage']]
    # Convert to numpy array
    data_np = df_set.values
    # Standardize data to zero mean and unit variance
    data = scale(data_np)
    # Specify number of clusters (based on silhouette score)
    k = 18
    # Create KMeans model and fit data
    kmeans = KMeans(n_clusters=k, n_init=25)
    kmeans.fit(data)
    score = silhouette_score(data, kmeans.labels_)
    labels = kmeans.labels_
    centroids = kmeans.cluster_centers_
    # Add cluster labels to dataframe
    df_set.insert(0,'Cluster',labels)
    # Add player name
    df_set.insert(0,'Player',df_in.Player)
    df = df_set.set_index('Player')
    # Insert column for similar players
    df.insert(0,'SimilarPlayers','')
    # Loop through clusters
    for i in range(k):
        # Pull out all players in the cluster
        players = df.ix[df.Cluster == i, ['Games_Played','Minutes_Per_Game','Points_Per_Game']]
        # Sort them based on minutes played, points, etc.
        sortPlayers = players.sort(columns = ['Minutes_Per_Game','Points_Per_Game','Games_Played'], ascending=False)
        playerList = sortPlayers.index.values.tolist()
        # Loop through players
        for player in playerList:
            # Find 3 nearest neighbors
            playerInd = playerList.index(player)
            if playerInd <= 2:
                df.loc[player,'SimilarPlayers'] = ', '.join(set(playerList[0:4])-set([playerList[playerInd]]))
            elif playerInd >= len(playerList)-3:
                df.loc[player,'SimilarPlayers'] = ', '.join(set(playerList[-4:])-set([playerList[playerInd]]))
            else:
                df.loc[player,'SimilarPlayers'] = ', '.join(set(playerList[playerInd-2:playerInd+2])-set([playerList[playerInd]]))
    # Simplify dataframe for saving
    df_csv = df['SimilarPlayers']
    df_csv = df_csv.reset_index()
    df_csv = df_csv.drop_duplicates()
    # Write to CSV
    df_csv.to_csv('../../data/Predict_SimilarPlayers.csv', index=False)

"""----------------------------------------------------------------"""
def main():
    """
    Main function for running
    """
    classifyData()
    clusterData()


"""*******************************************************************
*                                                                    *
*                   Script Execution                                 *
*                                                                    *
*******************************************************************"""
if __name__ == '__main__':
    main()
