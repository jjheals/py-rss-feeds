''' 
--> QUICK GUIDE TO THE FUNCTIONS RSS_DB_Connection 

    RETRIEVING INFORMATION FROM THE REMOTE DB: 
        getAllFeeds() ........ get a list of all feed titles from the databse
        getAllTags() ......... get a list of all tags (as objects) from the database
        getAllArticles() ..... get a list of all articles (as objects) from the database

    SENDING NEW INFORMATION TO THE REMOTE DB
        addFeed(feed:RSS_Feed) ................................. add a feed to the database
        updateArticles(rssFeedTitle:str) ....................... update the articles for the given feed. Assumes feed exists in the database with the given title
        addTagsToArticle(article:Article, tagList:list[Tag]) ... add a list of tags to the given article
        newTagsFromExcel(pathToFile:str) ....................... add the tags from the given excel file to the DB, ignoring duplicates
        newTagSetsFromExcel(pathToFile:str)..................... add new tag sets from the given excel file to the DB, ignoring duplicates
        
'''

import mysql.connector as mysql
import pandas as pd
from FP_Classes.RSS_Feed import RSS_Feed
from FP_Classes.RSS_Feed import RSS_Article
from FP_Classes.Tag import Tag 
from hashlib import sha1
from enum import Enum

from FP_Classes.Feeds.BleepingComputer import BleepingComputerRSS
from FP_Classes.Feeds.Censys import CensysRSS
from FP_Classes.Feeds.CensysDir import CensysDirRSS
from FP_Classes.Feeds.DefenseDepartment import DefenseDeptRSS
from FP_Classes.Feeds.Microsoft import MicrosoftRSS
from FP_Classes.Feeds.NationalVulnDatabase import NVD_RSS
from FP_Classes.Feeds.NIST import NIST_RSS
from FP_Classes.Feeds.StateDepartment import StateDeptRSS
from FP_Classes.Feeds.TheHackerNews import HackerNewsRSS
from FP_Classes.FP_Exceptions.MySQLCxnError import MySQLCxnError



class QueryOption(Enum):
    AND:int  = 0
    OR:int   = 1
    XOR:int  = 2
    NAND:int = 3
    
class RSS_DB_Connection: 
    
    username:str
    password:str
    host:str
    database:str 

    # STATIC
    
    ''' feeds_divs_dict keeps track of the divs for each of the feeds so the RSS articles can be created accordingly

        KEY:VALUE -> feed_title: article_div
    '''
    feeds_divs_dict:dict = { 
        BleepingComputerRSS.BC_FeedTitle: BleepingComputerRSS.BC_Article.BC_ArticleDiv,   # BleepingComputer
        CensysRSS.CS_FeedTitle: CensysRSS.CS_Article.CS_ArticleDiv,                       # Censys
        CensysDirRSS.CS_FeedTitle: CensysDirRSS.CSDir_Article.CSDir_ArticleDiv,           # Censys Director
        DefenseDeptRSS.DoD_FeedTitle: DefenseDeptRSS.DoDArticle.DoD_ArticleDiv,           # Defense Department
        MicrosoftRSS.MS_FeedTitle: MicrosoftRSS.MS_Article.MS_ArticleDiv,                 # Microsoft 
        NVD_RSS.NVD_FeedTitle: NVD_RSS.NVD_Article.NVD_ArticleDiv,                        # NVD
        NIST_RSS.NIST_FeedTitle: NIST_RSS.NIST_Article.NIST_ArticleDiv,                   # NIST
        StateDeptRSS.SD_FeedTitle: StateDeptRSS.SDCT_Article.SDCT_ArticleDiv,             # State Deptartment
        HackerNewsRSS.HN_FeedTitle: HackerNewsRSS.HN_Article.HN_ArticleDiv                # HackerNews
    }
    
    def __init__(self, username:str, password:str, host:str):
        self.username=username          # Given username
        self.password=password          # Given password
        self.host=host                  # Given host
        self.database='RSS_Feeds'       # Static database

    def new_connection(self) -> object: 
         # Create the connection and cursor
        try: 
            cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database)
            cursor = cxn.cursor()
            return cxn, cursor
        except Exception as e: 
            print(f"ERROR in RSS_DB_Connection.update_index(): There was an error initiating the database connection. Quitting.")
            print(e)
            raise MySQLCxnError()
    
    
        
    # -------------------------------------------------------------------------------------------------------------- #
    # INVERTED INDEX 
    
    def update_index(self, articles:list[RSS_Article]) -> bool:
        
         # Create the connection and cursor
        try: cxn, cursor = self.new_connection()
        except MySQLCxnError as e:  
            print(e)
            return False
        
        
        # Iterate over the articles and insert one by one into ARTICLE, then tokenize and update INVERTED_INDEX
        for a in articles: 
            
            # Format the insert statement into ARTICLE
            new_article_query:str = "INSERT IGNORE INTO ARTICLE(feed_title, article_title, article_link, pub_date, article_desc, article_content) VALUES"
            new_article_query += f"(\"{a.feed_title}\", \"{a.article_title}\", \"{a.article_link}\", \"{a.pub_date}\", \"{a.article_desc}\", \"{a.raw_content}\")"
            
            # Try to execute the insert into ARTICLE statement
            try: 
                cursor.execute(new_article_query)
                cxn.commit()
            except Exception as e:  
                # If the insert into ARTICLE statement fails, then skip the rest of this article since the FK constraints will fail
                print(f"ERROR in RSS_DB_Connection.update_index(): There was an error executing the insert statement (ARTICLE_TABLE) for \"{a.article_title}\". Moving on.")
                print(new_article_query)
                print(e)
                continue
            
            # Format the query to add the article tokens to INVERTED_INDEX table
            # Get the ID of the last inserted document
            cursor.execute("SELECT LAST_INSERT_ID()")
            article_id = cursor.fetchone()[0]
            
            # Insert tokens and article_content into the INVERTED_INDEX table
            insert_query = "INSERT IGNORE INTO INVERTED_INDEX(term, article_id, freq) VALUES (%s, %s, %s)"
            tokens_data = [(t, article_id, f) for t,f in a.article_tokens.items()]
            
            try: 
                cursor.executemany(insert_query, tokens_data)
                cxn.commit()
            except Exception as e: 
                print(f"ERROR in RSS_DB_Connection.update_index(): There was an error executing the insert statement (INVERTED_INDEX table) for \"{a.article_title}\". Moving on.")
                print(insert_query)
                print(e)
                continue
        
        # Done with the loop - close cursor and cxn
        cursor.close()
        cxn.commit()
        cxn.close()
        
        return True
    
    def query_articles(self, terms:list[str], op:QueryOption=QueryOption.AND) -> list[tuple]: 
        
        # Make sure some search terms were given
        if not terms: 
            print("RSS_DB_Connection.query_articles(): Empty set of terms given.")
            return []
        
        # Stem query terms 
        tokens, strn = RSS_Article.__contentPreprocessing__(" ".join(terms))
        
        match(op): 
            case QueryOption.AND: op_str:str = "&&"
            case QueryOption.OR: op_str:str = "||"
            case QueryOption.XOR: op_str:str = ""       # IMPLEMENT !!!
            
        # Init connection to DB
        try: cxn, cursor = self.new_connection()
        except MySQLCxnError as e: 
            print(e) 
            return []

        # Format the query
        query:str = f"SELECT DISTINCT ARTICLE.article_id, article_title, article_link, article_desc FROM ARTICLE NATURAL JOIN INVERTED_INDEX WHERE term = \"{list(tokens.keys())[0].lower()}\""
        
        for t in list(tokens.keys())[1:]: query += f" {op_str} term = \"{t.lower()}\""
        
        print(f"QUERY:\n{query}\n")
        
        # Execute the query
        try: cursor.execute(query)
        except Exception as e: 
            print("There was an error executing the query. Query:\n" + query)
            print(e)
            return []
        
        lst:list[tuple] = []
        for r in cursor.fetchall(): 
            lst.append((r[0],       # article_id
                        r[1],       # article_title
                        r[2],       # article_link
                        r[3])       # article_desc
                    )
        
        # Commit and close 
        RSS_DB_Connection.commit_close(cxn, cursor)
        
        return lst
        
            
        
        
    # -------------------------------------------------------------------------------------------------------------- #
    # Methods to GET information from the remote DB 
     
    ''' getAllFeeds() - get a list of all feed titles to perform further queries on, such as "updateArticles" 
        :return a list of feed titles
    '''
    def getAllFeeds(self) -> list[str]: 
        # Create the connection and cursor 
        cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database)
        cursor = cxn.cursor()
        
        query:str = "SELECT feed_title FROM RSS_FEED"   # Format the query
        cursor.execute(query)                           # Execute the query
        result = cursor.fetchall()                      # Get the result first
        allFeeds:list[str] = []                         # The list we will eventually return
        
        # The result is a list of tuples due to the way mysql works, so reformat the results to what we want
        # i.e., a list of strings [the feed titles]
        for r in result: allFeeds.append(r[0])     
        
        # Close the cursor and connection
        cursor.close()
        cxn.close() 
        
        # Return the final list     
        return allFeeds
    
    ''' getAllTags() - get a list of all tags (as objects) that currently exist in the DB 
        :return a list of tags
    '''
    def getAllTags(self) -> list[Tag]: 
        
        # Create the connection and cursor
        cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database)
        cursor = cxn.cursor()
        
        # Format and execute query
        query:str = "SELECT * FROM TAG"
        cursor.execute(query)
        
        # Get all the results and create tag objects 
        lot:list[Tag] = []                                              # List of tag objects to return
        for t in cursor.fetchall(): lot.append(Tag(t[0], t[1], t[2]))   # t[0] = tagName, t[1] = tagDesc, t[2] = caseSensitive
        return lot                                                      # Return the complete list
        
    ''' getAllArticles(feedTitle) - get a list of all RSS_Articles (as objects) in the database, optionally specifying a specific feed title
        :param feedTitle [optional] feed title to filter results
        :return a list of articles
    '''
    def getAllArticles(self, feedTitle="") -> list[RSS_Article]: 
        
        # Create the connection and cursor
        cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database)
        cursor = cxn.cursor()
        
        # Format and execute the query
        articlesQuery:str = "SELECT * FROM ARTICLE" 
        if feedTitle: articlesQuery += f" WHERE feed_title = \"{feedTitle}\""
        
        try: cursor.execute(articlesQuery)
        except Exception as e: 
            print(f"ERROR in RSS_DB_Connection.getAllArticles(): There was an error executing the articlesQuery. Quitting.")
            print(e)
            cursor.close()
            cxn.close()
            return []
        
        # Get the results from the cursor and transform them into Article objects
        articlesResults = cursor.fetchall()
        allArticles:list[RSS_Article] = []
        
        for r in articlesResults: 
            thisArticle:RSS_Article = RSS_Article(self.feeds_divs_dict[r[0]], r[0], r[1], r[2], r[3], r[4])                         # This article object WITHOUT TAGS yet
            #getTagsQuery:str = f"SELECT tag_name FROM TAG_FOR_ARTICLE WHERE article_title = \"{r[1]}\""   # Create the query to get the tags

            try: 
                #cursor.execute(getTagsQuery)                              # Execute the query to get these tags
                #tagsResults = cursor.fetchall()                           # Fetch results from the query
                #for t in tagsResults: thisArticle.tags.append(t[0])          # Add the results of the tags query to the Article as strings (tag names)
                allArticles.append(thisArticle)                           # Add this article to the list
                
            except Exception as e: 
                print(f"ERROR in RSS_DB_Connection: There was an error executing the query to get tags for the article title {thisArticle.article_title}. Continuing with the rest...")
                print(e)
                continue

        # Close connections and return the final list of Articles
        cursor.close()
        cxn.close()
        return allArticles 
    
    
    ''' getArticlesForTags(tag_names) - get a list of all RSS_Articles (as objects) from the database
        :param tag_names:list[str] list of tag names 
    '''
    def getArticlesForTags(self, tag_names:list[str]) -> list[RSS_Article]:
        # Check if a valid list of tag names was given
        if not tag_names: 
            print("ERROR in RSS_DB_Connection.getArticlesForTags(): No tag names were given. Quitting.")
            return []
        
        # Create the connection and cursor
        try: 
            cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database)
            cursor = cxn.cursor()
        except Exception as e: 
            print(f"ERROR in RSS_DB_Connection.getArticlesForTags(): There was an error initiating the database connection. Quitting.")
            print(e)
            return []
            
        # Format the query
        query:str = f"SELECT tag_name, feed_title, article_title, article_link, article_desc, pub_date, article_content FROM TAG_FOR_ARTICLE NATURAL JOIN ARTICLE WHERE tag_name = \"{tag_names[0]}\""
        
        for t_name in tag_names[1:]: query += f" || tag_name = \"{t_name}\""
        
        # Execute the query
        try: cursor.execute(query)
        except Exception as e: 
            print("ERROR in RSS_DB_Connection.getArticlesForTag(): There was an error executing the query. Quitting.")
            print(e)
            print("QUERY:\n" + query)
            cursor.close()
            cxn.close()
            return []
        
        # Get the results 
        articles:dict[str, RSS_Article] = {}     # Dict of key,value -> article_title,RSS_Article
        results = cursor.fetchall()              # Fetch results
        
        for r in results: 
            thisTitle = r[2]    # r[2] = article_title
            
            # Check if we've seen this title before since every article can have many tags
            if thisTitle in articles.keys(): articles[thisTitle].tags.append(r[0])   # r[0] = tag_name 
            
            # If we have NOT seen this article before then create a new RSS_Article object for it in articles
            else: 
                thisDiv = RSS_DB_Connection.feeds_divs_dict[r[1]]   # r[1] = feed_title
                
                # r[1] = feed_title, r[2] = article_title, r[3] = article_link, r[4] = pub_date, r[5] = article_desc
                thisArticle = RSS_Article(thisDiv, r[1], r[2], r[3], articlePubDate=r[4], articleDesc=r[5], process=False)
                thisArticle.tags.append(r[0])   # r[0] = tag_name
                
                articles[thisTitle] = thisArticle
                
        return articles
        
    ''' getAllArticleTitles() - get a list of all the article titles
        :return a list of strings (article_title)
    '''    
    def getAllArticleTitles(self, feedTitle:str="") -> list[str]:
        
        # Create the connection and cursor
        try: 
            cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database)
            cursor = cxn.cursor()
        except Exception as e: 
            print(f"ERROR in RSS_DB_Connection.getArticlesForTags(): There was an error initiating the database connection. Quitting.")
            print(e)
            return []
        
        # Execute the query
        query:str = "SELECT article_title FROM ARTICLE"
        if feedTitle: query += f" WHERE feed_title = \"{feedTitle}\""
        
        try: cursor.execute(query)
        except Exception as e: 
            print("ERROR in RSS_DB_Connection.getAllArticleTitles(): There was an error executing the query. Quitting.")
            print(e) 
            cursor.close()
            cxn.close()
            return []
        
        # Return the results
        results = cursor.fetchall()
        results = [r[0] for r in results]
        return results
    
    # -------------------------------------------------------------------------------------------------------------- # 
    # Methods to UPDATE information in the remote DB
    
    ''' addArticles(articles) - add a list of articles to the DB
        :param articles a list of RSS_Article 
        :return False if error, True if success
    '''
    def addArticles(self, articles:list[RSS_Article]) -> bool:
        
        # Base case: No articles to add
        if not articles: 
            print("NOTICE in RSS_DB_Connection.addArticles(): There are no provided articles. Returning.")
            return True
        
        # Try to create the cxn and cursor
        try: 
            cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database)
            cxn.autocommit = True
            cursor = cxn.cursor()
        except: 
            print("ERROR in RSS_DB_Connection.addArticles(): There was an error creating the connection or cursor. Exiting.")
            return False
        
        query:str = "INSERT IGNORE INTO ARTICLE(feed_title, article_title, article_link, pub_date, article_desc, article_content) VALUES"
        
        for a in articles: 
            a.sanitize()
            query += f"(\"{a.feed_title}\", \"{a.article_title}\", \"{a.article_link}\", \"{a.pub_date}\", \"{a.article_desc}\", \"{a.raw_content}\"),"
        
        query = query[:-1]
        
        try: cursor.execute(query)
        except Exception as e: 
            print(f"ERROR in RSS_DB_Connection.addArticles(): there was an error executing the insert query. Exiting.")
            print(e)
            print(f"Insert statement: {query}")
            cursor.close()
            cxn.close()
            return False
        
        print("NOTICE: Articles added successfully.")
        cursor.close()
        cxn.commit()
        cxn.close()
        return True
            

    ''' addFeed(rss_feed) - add a new feed to the database
        :param rss_feed an instance of RSS_Feed
        :param updateArticles bool whether to automatically update/add the articles for this feed to the DB
        :return False if error, True if success
    '''
    def addFeed(self, rss_feed:RSS_Feed, threadLimit=99999, updateArticleTags=[]) -> bool:
        
        # Try to create the cxn and cursor
        try: 
            cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database)
            cursor = cxn.cursor()
        except: 
            print("ERROR in RSS_DB_Connection.addFeed(): There was an error creating the connection or cursor. Exiting.")
            return False
        
        # Run an INSERT IGNORE statement for the feed
        try: 
            query:str = f"INSERT IGNORE INTO RSS_FEED(feed_title, feed_link, feed_desc) VALUES(\"{rss_feed.feed_title}\", \"{rss_feed.feed_link}\", \"{rss_feed.feed_desc}\")"
            cursor.execute(query)
        except Exception as e:
            print("ERROR in RSS_DB_Connection.addFeed(): There was an error executing the query. Exiting.")
            print(e)
            cursor.close()
            cxn.close()
            return False
        
        # Print success notices and close the cursor
        print(f"NOTICE in RSS_DB_Connection.addFeed(): Add feed query executed successfully for \"{rss_feed.feed_title}\" - Either the feed was added or already exists in the database. Closing cursor.")
        
        # Commit the results and close the cursor
        cxn.commit()
        cursor.close()
        cxn.close()
        
        if updateArticleTags: 
            print(f"\nNOTICE in RSS_DB_Connection.addFeed(): updateArticles is turned on - calling updateArticles() for the feed \"{rss_feed.feed_title}\".")
            self.updateArticles(rss_feed, updateArticleTags, threadLimit)
        
        return True
        
    ''' updateArticles(rssFeed) - update the articles for the given RSS feed title
        :param rssFeed an RSS_Feed object
        :return False if error, True if success
        
        NOTE: This method assumes the RSS feed exists in the DB and will throw an error (return false) if it does not.
    '''
    def updateArticles(self, rssFeed:RSS_Feed, tags:list[Tag]) -> bool:
        
        try: cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database, autocommit=True)
        except: 
            print("ERROR in RSS_DB_Connection.updateArticles(): there was an error creating the connection. Exiting.")
            return False
        
        try: cursor = cxn.cursor()
        except: 
            print("ERROR in RSS_DB_Connection.updateArticles(): there was an error creating the cursor. Exiting.")
            cxn.close()
            return False
        
        # - - - - - - - - - - - - - - - - - - - - - - #
        # First make sure this feed exists so the foreign key restraints do not cause issues
        if not RSS_DB_Connection.__testFeedExists__(cxn, cursor, rssFeed.feed_title): return False
 
        # - - - - - - - - - - - - - - - - - - - - - - #
        # Format the base queries for this feed's articles
        
        # Query for adding the articles to the ARTICLES table
        articlesQuery = "INSERT IGNORE INTO ARTICLE(feed_title, article_title, article_link, pub_date, article_desc) VALUES"
        articlesValues = ""
        
        # Query for adding the tags for all of these articles to the ARTICLES_TAGS table
        articlesTagsQuery = "INSERT IGNORE INTO TAG_FOR_ARTICLE(id, article_title, tag_name) VALUES"
        articlesTagsValues = ""
        
        # - - - - - - - - - - - - - - - - - - - - - - #
        # For every article, add the appropriate strings to the values queries
        print(f"[+] Classifying and formatting queries for articles from feed: {rssFeed.feed_title}")

        # Loop through the articles and classify all of them
        for a in rssFeed.articles: 
            
            # 0. Classify the article
            a.classify(tags)     

            # 1. If the article does not have any tags, move on 
            if not a.tags: continue     
            
            # 2. Sanitize the article and add it to the articles query
            a = RSS_DB_Connection.sanitizeArticle(a)
            articlesValues += f"(\"{rssFeed.feed_title}\", \"{a.article_title}\", \"{a.article_link}\", \"{a.pub_date}\", \"{a.article_desc}\"),"
            
            # 3. Add the articles tags to the articlesTagsValues
            for t in a.tags: articlesTagsValues += f"(\"{sha1(f'{a.article_title}{t}'.encode()).hexdigest()}\", \"{a.article_title}\", \"{t}\"),"

        # - - - - - - - - - - - - - - - - - - - - - - #
        # Add the values strings to the base queries
    
        articlesQuery += articlesValues[:-1]       # Trim the trailing ',' 
        articlesTagsQuery += articlesTagsValues[:-1]    # Trim the trailing "," 
        
        # - - - - - - - - - - - - - - - - - - - - - - #
        # Try to execute the queries 
        try: 
            
            # Check if there are values to add 
            if not articlesValues: 
                print(f"NOTICE: Feed \"{rssFeed.feed_title} does not have any articles of interest. Exiting.")
                cursor.close()
                cxn.close()
                return True
                
            # Execute the articlesQuery first for the foreign key restraint
            print(f"\n[+] Updating database with articles for feed {rssFeed.feed_title}")
            cursor.execute(articlesQuery)       
            
            # Execute the articlesTagsQuery after 
            print(f"[+] Updating database with tags for articles from feed: {rssFeed.feed_title}")
            cursor.execute(articlesTagsQuery)   
            
        except Exception as e:
            print(f"ERROR in RSS_DB_Connection.updateArticles(): there was an error adding the articles and/or tags for {rssFeed.feed_title} to the DB. Exiting.\n")
            print("\t Articles query: \n\t" + articlesQuery)
            print("\tArticles Tags Query: \n\t" + articlesTagsQuery)
            print(e)
            cursor.close()
            cxn.close()
            return False
        
        print(f"NOTICE in RSS_DB_Connection.updateArticles(): new articles and tags for {rssFeed.feed_title} added to the DB successfully. Closing cursor.\n")
        
        # Commit the results and close the cursor 
        cursor.close()
        cxn.commit()
        cxn.close()
        
        return True    
    
    ''' addTagsToArticle(article, tagList) - add a list of tags to the given article
        :param article an article object 
        :param tagList a list of tag objects
        :return the updated Article object
    '''
    def addTagsToArticles(self, articles:list[RSS_Article]) -> list[RSS_Article]: 
        cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database, autocommit=True)
        cursor = cxn.cursor()

        # Perform the following for each article in articles list
        for article in articles:
           
            # Add the tags to the Article object and format the VALUES tuples for the query
            # NOTE: the ARTICLE_TAGS table uses a sha1 hash of the article_title + tag.tagName as the ID to make sure the same article
            #       isn't duplicate tagged, since mysql does not allow more than 1 primary key 
            tagList:list[str] = article.tags
            
            # Sanitize the article title so it does not contain any ' " '
            article = RSS_DB_Connection.sanitizeArticle(article)
            
            if not tagList: 
                print(f"NOTICE: Article \"{article.article_title}\" does not have any tags. Skipping.")
                continue
            
            valuesStr:str = ""
            for t in tagList: 
                valuesStr += f"(\"{sha1(f'{article.article_title}{t}'.encode()).hexdigest()}\", \"{article.article_title}\", \"{t}\"),"
            
            valuesStr = valuesStr[:-1] # Trim the trailing ","
            
            # Update the database 
            query = "INSERT IGNORE INTO TAG_FOR_ARTICLE(id, article_title, tag_name) VALUES" + valuesStr

            try: cursor.execute(query)
            except Exception as e: 
                print(f"ERROR in RSS_DB_Connection.addTagsToArticle(): There was an error with the insert statement for \"{article.article_title}\". The given Article's list of tags was locally updated but not the remote database. Moving on.")
                print(e)
                continue
            
        # Print success message and terminate connections
        print("NOTICE: Done with DB connection. Check output for errors. Quitting.\n")
        cursor.close()
        cxn.commit()
        cxn.close()
        return articles
    
    ''' newTagsFromExcel(path) - add new tags to the DB from an excel sheet 
        :param path path to the sheet
        :return False if error, True if success
    '''
    def newTagsFromExcel(self, pathToFile:str) -> bool: 
        print("\nNOTICE in RSS_DB_Connection.newTagsFromExcel(): called newTagsFromExcel() - beginning process.")
        
        # Get the dataframe from the excel file
        try: df = pd.read_excel(pathToFile)
        except Exception as e:
            print(f"ERROR in RSS_DB_Connection.newTagsFromExcel(): there was an error reading the excel file. Quitting.")
            print(e)
            return False
        
        # Initiate connection and create cursor
        try: 
            cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database, autocommit=True)
            cursor = cxn.cursor()
        except Exception as e: 
            print("ERROR in RSS_DB_Connection.newTagsFromExcel(): there was an error initiating the DB connection. Quitting.")
            print(e)
            return False
        
        print("NOTICE in RSS_DB_Connection.newTagsFromExcel(): excel sheet read and DB connection established successfully. Formatting query...")
        
        # Format the queries
        tagQuery = "INSERT IGNORE INTO TAG(tag_name, tag_desc, case_sensitive) VALUES"
        tagInSetQuery = "INSERT IGNORE INTO TAG_IN_SET(id, tag_name, set_name) VALUES"
        
        for r in df.values: 
            thisTagName:str = r[0]
            thisSet:str = r[3]
            
            tagQuery += f"(\"{str(r[0]).rstrip()}\", \"{r[1]}\", {str(r[2]).lower()}),"
            if thisSet: tagInSetQuery += f"(\"{sha1(f'{thisSet}{thisTagName}'.encode()).hexdigest()}\", \"{thisTagName.rstrip()}\", \"{str(thisSet).rstrip()}\"),"
            
        tagQuery = tagQuery[:-1]
        tagInSetQuery = tagInSetQuery[:-1]

        # Execute the query
        try: 
            cursor.execute(tagQuery)
            cursor.execute(tagInSetQuery)
        except Exception as e: 
            print(f"ERROR in RSS_DB_Connection.newTagsFromExcel(): there was an error adding the new tags or sets to the database. Terminating connections.")
            print(e)
            cursor.close()
            cxn.close()
            return False
        
        print("NOTICE in RSS_DB_Connection.newTagsFromExcel(): new tag queries formatted and executed successfully. Terminating connections and quitting.")
        cursor.close()
        cxn.commit()
        cxn.close()
        print("SUCCESS.")
        return True
    
    ''' newTagSetsFromExcel(path) - add the new tag sets to the DB from an excel sheet '''
    def newTagSetsFromExcel(self, pathToFile:str) -> bool: 
        print("\nNOTICE in RSS_DB_Connection.newTagsFromExcel(): called newTagsFromExcel() - beginning process.")
        
        # Get the dataframe from the excel file
        try: df = pd.read_excel(pathToFile)
        except Exception as e:
            print(f"ERROR in RSS_DB_Connection.newTagSetsFromExcel(): there was an error reading the excel file. Quitting.")
            print(e)
            return False
        
        # Initiate connection and create cursor
        try: 
            cxn = mysql.connect(username=self.username, password=self.password, host=self.host, database=self.database, autocommit=True)
            cursor = cxn.cursor()
        except Exception as e: 
            print("ERROR in RSS_DB_Connection.newTagSetsFromExcel(): there was an error initiating the DB connection. Quitting.")
            print(e)
            return False
        
        print("NOTICE in RSS_DB_Connection.newTagSetsFromExcel(): excel sheet read and DB connection established successfully. Formatting query...")
        
        # Format the query
        query = "INSERT IGNORE INTO TAG_SET(set_name, set_desc) VALUES"
        
        for r in df.values: 
            query += f"(\"{str(r[0]).rstrip()}\", \"{r[1]}\"),"
            
        query = query[:-1]
        
        # Execute the query
        try: 
            cursor.execute(query)
        except Exception as e: 
            print(f"ERROR in RSS_DB_Connection.newTagSetsFromExcel(): there was an error adding the new tag sets to the database. Terminating connections.")
            print(e)
            cursor.close()
            cxn.close()
            return False
        
        print("NOTICE in RSS_DB_Connection.newTagSetsFromExcel(): new tag set query formatted and executed successfully. Terminating connections and quitting.")
        cursor.close()
        cxn.commit()
        cxn.close()
        print("SUCCESS.")
        return True
    
    # -------------------------------------------------------------------------------------------------------------- # 
    # STATIC METHODS 
    
    ''' sanitizeArticle(article) - sanitize the article's title and description to not contain illegal characters
        :param article an RSS_Article obj 
        :return the article obj with sanitized title and description  
    '''
    @staticmethod
    def sanitizeArticle(article:RSS_Article) -> RSS_Article: 
        article.article_title = article.article_title.replace("\"", "")
        article.article_desc = article.article_desc.replace("\"", "")
        return article
    
    ''' __testFeedExists__(cxn, cursor, feedTitle) - check if the given feed title exists in the DB
        :param cxn a mysql.MySQLConnection instance 
        :param cursor a mysql.cursor instance 
        :param feedTitle the feed title to look for 
        :return False if the feed does not exist, true if it does
    '''
    @staticmethod
    def __testFeedExists__(cxn:mysql.MySQLConnection, cursor, feedTitle:str) -> bool: 
        query = f"SELECT * FROM RSS_FEED WHERE feed_title = \"{feedTitle}\""
        cursor.execute(query)
        
        # Check if we got results 
        row = cursor.fetchone()
        if row is None:
            print(f"ERROR in RSS_DB_Connection.__testFeedExists__(): test query did not find any existing RSS feeds for {feedTitle}. Exiting.")
            cursor.close()
            cxn.close()
            return False
        else: 
            # We got results
            print(f"NOTICE in RSS_DB_Connection.__testFeedExists__(): test query found at least one result for \"{feedTitle}\". Proceeding.")
            return True


    @staticmethod
    def commit_close(cxn, cursor) -> bool: 
        try: 
            cursor.close()
            cxn.commit()
            cxn.close()
            return True
        except Exception as e:
            print(f"ERROR in RSS_DB_Connection.update_index(): There was an error closing the database connection. Quitting.")
            print(e)
            return False