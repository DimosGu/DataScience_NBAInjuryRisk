"""
----------------------------------------------------------------------
    scrapeData.py
----------------------------------------------------------------------
    Scrapes data from the web and stores results in csv files

    NOTE: SportVU player tracking data from stats.nba.com was
    collected using Kimono (https://www.kimonolabs.com/) and
    downloaded directly as csv files
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2014-08-06
----------------------------------------------------------------------
"""

import urllib2
import time
import string
import re
from datetime import datetime
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd


class Scraper:
    """
    A class to scrape baksetball websites and create CSV files
    """

    def getPlayerLinks_NBA(self):
        """
        Create a dictionary mapping the player name (First Last) to
        their playerfile link
        """
        # Base URL
        url = 'http://stats.nba.com/players.html#ap-L'
        # Open the URL and read
        response = urllib2.urlopen(url)
        page_source = response.read()
        # Soupify the page
        soup = BeautifulSoup(page_source)
        # Get directories of players
        # (First directory has active players, second has historical players)
        active_div = soup.find_all("div", attrs = {"class":"directory"})
        # Pull out the links in the directory
        player_a_list = active_div[0].find_all("a", attrs = {"class":"playerlink"})
        # Get the link to the playerfile page
        player_links = [player_a["href"] for player_a in player_a_list]
        # Get the name (Last, First)
        player_lastfirst = [player_a.find(text=True) for player_a in player_a_list]
        # Reorder the names appropriately
        player_names = [player_lf.split(", ")[1]+" "+player_lf.split(", ")[0]
                        if len(player_lf.split(", ")) > 1 else player_lf
                        for player_lf in player_lastfirst]
        # Dictionary of player names and links
        player_dict = {'Player':player_names, 'ProfileURL':player_links}
        # Add to instance
        self.playerLinksNBA = player_dict
        # Convert to dataframe
        player_df = pd.DataFrame(player_dict)
        player_df = player_df.set_index('Player')
        # Save to CSV
        player_df.to_csv('../../data/NBA_Player_ProfileLinks__RAW.csv')

    """------------------------------------------------------------"""
    def getDemographics_NBA(self):
        """
        Create a dictionary mapping the player name (First Last) to their
        demographic information - height, weight, birthdate, etc.
        """
        # Initialize dictionary
        player_dict = {}
        colNames = ['Height', 'Weight', 'BirthDate', 'YearsPro', 'Team', 'JerseyNum', 'Position', 'PictureURL', 'StatsURL']
        # Iterate through playerfile links
        for i, player_url in enumerate(self.playerLinksNBA['ProfileURL']):
            player_name = self.playerLinksNBA['Player'][i]
            # Handle error
            try:
                # Open the URL and read
                response = urllib2.urlopen(player_url)
                page_source = response.read()
                # Soupify the page
                soup = BeautifulSoup(page_source)
                # Link to stats
                stats_url_list = soup.find_all("a", attrs = {"id":"tab-stats"})
                stats_url = stats_url_list[0]["href"]
                # Jersey number and position
                num_position = soup.find("h2", attrs = {"class":"num-position"}).find(text=True).strip()
                num, position = num_position.split(' | ')
                # Current team
                team = soup.find("h3", attrs = {"class":"player-team"}).find(text=True).strip()
                # Height and weight data have same class
                height_weight = soup.find_all("span", attrs = {"class":"nbaHeight"}) # e.g. [6'3", 185 lbs.]
                # Convert height to inches
                height = int(height_weight[0].find(text=True).strip().split("'")[0])*12 + int(height_weight[0].find(text=True).strip().split("'")[1][0])
                # Strip 'lbs' from weight
                weight = int(height_weight[1].find(text=True).strip().split(' ')[0])
                # Birthdate
                birthdate_str = soup.find("span", attrs = {"itemprop":"birthDate"}).find(text=True).strip() # e.g. March 14, 1988
                birthdate = datetime.date(datetime.strptime(birthdate_str, '%B %d, %Y'))
                # Years pro
                yearspro = int(soup.find("span", text = u'Years Pro:').next_sibling.next_sibling.find(text=True))
                # URL to profile picture
                picture_url = soup.find("div", attrs = {"class":"player-headshot"}).find("img")["src"]
                # Build dictionary
                demographic_dict = dict(zip(colNames, [height, weight, birthdate, yearspro, team, num, position, picture_url, stats_url]))
                player_dict[player_name] = demographic_dict
                print 'Finished processing ' + player_name
            except:
                player_dict[player_name] = dict(zip(colNames, [None, None, None, None, None, None, None, None, None]))
                print 'Error with ' + player_name
        # Convert to dataframe (make player names the row indices)
        player_df = pd.DataFrame(player_dict).transpose()
        player_df.index.names = ['Player']
        try:
            player_df = player_df[colNames]
        except:
            pass
        # Add to instance
        self.demographicsNBA = player_df
        # Save to CSV
        player_df.to_csv('../../data/NBA_Player_Demographics__RAW.csv')

    """------------------------------------------------------------"""
    def getPlayerLinks_BR(self):
        """
        Map current players to URL's at basketball-reference
        """
        names_urls = []
        # Go through all letters
        for letter in string.ascii_lowercase:
            # URL
            url = 'http://www.basketball-reference.com/players/' + letter + '/'
            try:
                # Open the URL and read
                response = urllib2.urlopen(url)
                page_source = response.read()
                # Soupify the page
                soup = BeautifulSoup(page_source)
                # Currently active players
                current_players = soup.find_all('strong')
                # Loop through current names
                for name in current_players:
                    name_data = name.children.next()
                    names_urls.append((name_data.contents[0], 'http://www.basketball-reference.com' + name_data.attrs['href']))
                # Pause
                time.sleep(1)
            except:
                pass
        # Convert to dataframe
        br_df = pd.DataFrame(names_urls, columns=['Player','URL'])
        # Add to instance
        self.playerLinksBR = br_df
        # Save to CSV
        br_df.to_csv('../../data/BR_Player_Links__RAW.csv', index=False, encoding='utf-8')

    """------------------------------------------------------------"""
    def getDemographics_BR(self):
        """
        Get player (all) demographics from basketball-reference
        """
        table_data = []
        # Go through all letters
        for letter in (string.ascii_lowercase[:-3]+string.ascii_lowercase[-2:]): # ignore x
            # URL
            url = 'http://www.basketball-reference.com/players/' + letter + '/'
            # Open the URL and read
            response = urllib2.urlopen(url)
            page_source = response.read()
            # Soupify the page
            soup = BeautifulSoup(page_source)
            table = soup.find("table", attrs = {"id":"players"})
            table_rows = table.findAll("tr")
            # Extract header information on first run of loop
            if letter == 'a':
                cells = table_rows[0].find_all("th")
                table_header = []
                for c in cells:
                    table_header.append(c.find(text=True))
                table_header.insert(1,u'URL')
            # Iterate through each row and extract text in each cell
            for row in range(1, len(table_rows)):
                cells = table_rows[row].find_all("td")
                row_data = []
                for i, cell in enumerate(cells):
                    if i == 0:
                        row_data.append(cell.find(text=True))
                        row_data.append(u'http://www.basketball-reference.com' + cell.a['href'])
                    elif i == 4:
                        heightStr = cell.find(text=True)
                        height = 12*int(heightStr.split('-')[0]) + int(heightStr.split('-')[1])
                        row_data.append(height)
                    else:
                        row_data.append(cell.find(text=True))
                table_data.append(row_data)
            print 'Finished processing the letter ' + letter.upper()
        df = pd.DataFrame(table_data, columns=table_header)
        df.drop('College', axis=1, inplace=True)
        # Rename columns
        df = df.rename(columns = {'Birth Date':'BirthDate', 'From':'FromYear', 'To':'ToYear', 'Ht':'Height', 'Wt':'Weight'})
        # Add to instance
        self.demographicsBR = df
        # Save to CSV
        df.to_csv('../../data/BR_Player_Demographics__RAW.csv', index=False, encoding='utf-8')

    """------------------------------------------------------------"""
    def getGameLogLinks_BR(self):
        """
        Get links to all game logs for all players who've played since 2010
        """
        df = self.demographicsBR
        # Drop players who didn't play in the last 4 seasons
        df = df[df.ToYear > 2010]
        df.set_index(np.arange(0, len(df)), inplace=True)
        name_urls = []
        for i, player_url in enumerate(df.URL.tolist()):
            name = df.Player[i]
            # Open the URL and read
            response = urllib2.urlopen(player_url)
            page_source = response.read()
            # Soupify the page
            soup = BeautifulSoup(page_source)
            # Return list of game log <a> tags
            aList = soup.find(text=u'Game Logs').parent.next.next.next.next.findAll('a')
            # Get links
            links = [u'http://www.basketball-reference.com' + aTag.get('href') for aTag in aList]
            years = [int(link.split('/')[-2]) for link in links]
            # Append to big list
            for j, link in enumerate(links):
                name_urls.append((name, years[j], link))
            # Pause
            time.sleep(1)
            print 'Finished processing ' + name
        # Convert to dataframe
        newDF = pd.DataFrame(name_urls, columns=['Player','Year','URL'])
        # Add to instance
        self.gameLogLinksBR = newDF
        # Save to CSV
        newDF.to_csv('../data/BR_Player_GameLogLinks__RAW.csv', index=False)

    """------------------------------------------------------------"""
    def getGameLogs_BR(self):
        """
        Get game logs since 2010 for all players
        """
        df = self.gameLogLinksBR
        df = df[df.Year >= 2010]
        df.set_index(np.arange(0, len(df)), inplace=True)
        # Loop through every player
        for i, url in enumerate(df.URL.tolist()):
            # Player name
            name = df.Player[i]
            # Year
            year = df.Year[i]
            # Open the URL and read
            response = urllib2.urlopen(url)
            page_source = response.read()
            # Soupify the page
            soup = BeautifulSoup(page_source)
            # ----------------
            def soupTableToDF(table_soup, header):
                # Parses the HTML/Soup table for the gamelog stats.
                # Returns a pandas DataFrame
                if not table_soup:
                    return None
                else:
                    try:
                        rows = table_soup[0].findAll('tr')[1:]  # all rows but the header
                        # remove intermediary header rows
                        rows = [r for r in rows if len(r.findAll('td')) > 0]
                        parsed_table = [[col.getText() for col in row.findAll('td')] for row in rows] # build 2d list of table values
                        return pd.DataFrame(parsed_table, columns=header)
                    except:
                        return None
            # ----------------
            reg_season_table = soup.findAll('table', attrs={'id': 'pgl_basic'})  # id for reg season table
            playoff_table = soup.findAll('table', attrs={'id': 'pgl_basic_playoffs'}) # id for playoff table
            # Parse the table header
            try:
                header = []
                for th in reg_season_table[0].findAll('th'):
                    if not th.getText() in header:
                        header.append(th.getText())
                # Add in headers for home/away and w/l columns to get the DataFrame to parse correctly
                header[5] = u'HomeAway'
                header.insert(7, u'WinLoss')
                reg = soupTableToDF(reg_season_table, header)
                # Add column for regular season vs. playoffs; add column for player name
                if reg is not None:
                    reg.insert(0, u'Season', u'Regular')
                    reg.insert(0, u'Year', year)
                    reg.insert(0, u'Player', name)
                playoff = soupTableToDF(playoff_table, header)
                if playoff is not None:
                    playoff.insert(0, u'Season', u'Playoffs')
                    playoff.insert(0, u'Year', year)
                    playoff.insert(0, u'Player', name)
            except:
                reg = None
                playoff = None
            # Append to big dataframe
            if i == 0:
                if reg is None:
                    final_df = playoff
                elif playoff is None:
                    final_df = reg
                else:
                    final_df = pd.concat([reg, playoff])
            else:
                if reg is None:
                    final_df = pd.concat([final_df, playoff])
                elif playoff is None:
                    final_df = pd.concat([final_df, reg])
                else:
                    final_df = pd.concat([final_df, reg, playoff])
            # Message to user
            print 'Finished ' + name + ' ' + str(year)
            # Save periodically
            if i in range(len(df.URL.tolist()), 10):
                final_df.to_csv('../../data/BR_Player_GameLogs__TEMP.csv', index=False)
                print '******* Saved at index ' + str(i)
        # Update Home/Away column
        final_df.HomeAway[final_df.HomeAway == u'@'] = u'Away'
        # Add column for DidNotPlay (Boolean)
        final_df.insert(6, u'DidNotPlay', False)
        final_df.DidNotPlay[final_df.GS == u'Did Not Play'] = True
        final_df.DidNotPlay[final_df.GS == u'Player Suspended'] = True
        # Add column for Inactive (Boolean)
        final_df.insert(6, u'Inactive', False)
        final_df.Inactive[final_df.GS == u'Inactive'] = True
        # Update GS
        final_df.GS[final_df.GS == u'Inactive'] = np.nan
        final_df.GS[final_df.GS == u'Did Not Play'] = np.nan
        final_df.GS[final_df.GS == u'Player Suspended'] = np.nan
        # Save to CSV
        final_df.to_csv('../../data/BR_Player_GameLogs__RAW.csv', index=False)

    """------------------------------------------------------------"""
    def getStatsSummary_BR(self):
        """
        Get season summaries for players from basketball-reference
        """
        df = self.demographicsBR
        # Drop players who didn't play in the last 4 seasons
        df = df[df.ToYear > 2010]
        df.set_index(np.arange(0, len(df)), inplace=True)
        # Loop
        for i, player_url in enumerate(df.URL.tolist()):
            # Player name
            name = df.Player[i]
            # Open the URL and read
            response = urllib2.urlopen(player_url)
            page_source = response.read()
            # Soupify the page
            soup = BeautifulSoup(page_source)
            if not soup:
                print 'Problem soupifying ' + name
                continue
            # ----------------
            def soupTableAndHeaderToDF(soup, tableID, rowRegex):
                tableFind = soup.find('table', id=tableID)
                if not tableFind:
                    return None
                else:
                    tableHeader = tableFind.findAll('th')
                    header = []
                    for th in tableHeader:
                        header.append(re.sub('%', 'pct', th.getText()))
                    allrows = soup.findAll('tr', id=re.compile(rowRegex))
                    parsed_table = [[col.getText() for col in row.findAll('td')] for row in allrows]
                    df = pd.io.parsers.TextParser(parsed_table, names=header, parse_dates=True).get_chunk()
                    df['Season'] = df['Season'].map(lambda x: x[:7])
                    df.insert(0, u'Player', name)
                    return df
            # ----------------
            # Regular Season Totals
            reg_totals_df = soupTableAndHeaderToDF(soup, 'totals', '^totals[.]\d+')
            # Regular Per Game summaries
            reg_pergame_df = soupTableAndHeaderToDF(soup, 'per_game', '^per_game[.]\d+')
            # Playoffs Totals
            playoffs_totals_df = soupTableAndHeaderToDF(soup, 'playoffs_totals', '^playoffs_totals[.]\d+')
            # Playoffs Per Game summaries
            playoffs_pergame_df = soupTableAndHeaderToDF(soup, 'playoffs_per_game', '^playoffs_per_game[.]\d+')
            # ----------------
            def joinDataframes(df, dfAll):
                if dfAll is not None:
                    if df is not None:
                        dfNEW = pd.concat([dfAll, df])
                    else:
                        dfNEW = dfAll
                else:
                    if df is not None:
                        dfNEW = df
                    else:
                        dfNEW = None
                return dfNEW
            # ----------------
            # Append to big dataframe
            reg_totals_df_ALL = joinDataframes(reg_totals_df, reg_totals_df_ALL)
            reg_pergame_df_ALL = joinDataframes(reg_pergame_df, reg_pergame_df_ALL)
            playoffs_totals_df_ALL = joinDataframes(playoffs_totals_df, playoffs_totals_df_ALL)
            playoffs_pergame_df_ALL = joinDataframes(playoffs_pergame_df, playoffs_pergame_df_ALL)
            # Message
            print 'Done processing ' + name
        # ----------------
        def writeCSV(df, pathToCSV):
            if df is not None:
                df.to_csv('../../data/' + pathToCSV + '.csv', index=False)
        # ----------------
        # Write to CSV
        writeCSV(reg_totals_df_ALL, 'BR_Player_StatsSummary_RegularSeason_Total__RAW')
        writeCSV(reg_pergame_df_ALL, 'BR_Player_StatsSummary_RegularSeason_PerGame__RAW')
        writeCSV(playoffs_totals_df_ALL, 'BR_Player_StatsSummary_Playoffs_Total__RAW')
        writeCSV(playoffs_pergame_df_ALL, 'BR_Player_StatsSummary_Playoffs_PerGame__RAW')

    """------------------------------------------------------------"""
    def main(self):
        """
        Main function for running
        """
        self.getPlayerLinks_NBA()
        self.getDemographics_NBA()
        self.getPlayerLinks_BR()
        self.getDemographics_BR()
        self.getGameLogLinks_BR()
        self.getGameLogs_BR()
        self.getStatsSummary_BR()


"""*******************************************************************
*                                                                    *
*                   Script Execution                                 *
*                                                                    *
*******************************************************************"""
if __name__ == '__main__':
    # Create instance of class
    scraper = Scraper()
    # Run code
    scraper.main()
