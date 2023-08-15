
# General imports 
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article
from FP_Classes.RSS_DB_Connection import RSS_DB_Connection
from FP_Classes.Tag import Tag
import json
from threading import Thread 
from time import sleep

# Imports for cluster analysis 
from data_analysis.ClusteringTechniques import *

# ------------------------------------------------------------------------------ #
# All imports for all RSS feeds

from FP_Classes.Feeds.BleepingComputer import BleepingComputerRSS   # BleepingComputer
from FP_Classes.Feeds.Censys import CensysRSS                       # Censys (general)
from FP_Classes.Feeds.CensysDir import CensysDirRSS                 # Censys (director)
from FP_Classes.Feeds.DefenseDepartment import DefenseDeptRSS       # Department of Defense
from FP_Classes.Feeds.Microsoft import MicrosoftRSS                 # Microsoft 
from FP_Classes.Feeds.NationalVulnDatabase import NVD_RSS           # National Vulnerability Database
from FP_Classes.Feeds.NIST import NIST_RSS                          # NIST 
from FP_Classes.Feeds.StateDepartment import StateDeptRSS           # State Department (multiple feeds) - NOTE: This one takes a very long time so I removed it for now
from FP_Classes.Feeds.TheHackerNews import HackerNewsRSS            # Hacker News (news articles)

# ------------------------------------------------------------------------------ #
# Initialization of all variables
configDir = "config/"                  # Change if you changed the default file hierarchy 
feedThreads:dict[str, Thread] = {}      # To keep track of the threads still running and print their targets (the feed each is for) for debugging/logging purposes

# Get config settings
config = json.load(open(configDir + "config.json"))

# Get db credentials
try: db_creds = json.load(open(configDir + config['db-creds-json-path']))
except Exception as e: 
    print("CRITICAL ERROR: Error getting DB Creds. Quitting.")
    print(e)
    quit()

# Init DB connection
dbConn = RSS_DB_Connection(
            username=db_creds['username'],
            password=db_creds['password'],
            host=db_creds['host']
        )

# Get all tags and update DB 
allTags:list[Tag] = []
for d in json.load(open(configDir + config['tags-json-file'])): allTags.append(Tag.tagFromDict(d))

if not dbConn.newTagsFromExcel(configDir + config['update-tags-filepath']):
    print("CRITICAL ERROR: There was an error adding tags to the DB. Exiting program.")
    quit()
else: 
    print("SUCCESS: DB tags updated successfully.")

# Initialize all Feed objects 
bleepingComputerRss = BleepingComputerRSS()
censysRss = CensysRSS()
censysDirRss = CensysDirRSS()
defenseDeptRss = DefenseDeptRSS()
microsoftRss = MicrosoftRSS()
nvdRss = NVD_RSS()
nistRss = NIST_RSS()
stateDeptRss = StateDeptRSS()      # Intentionally commented out - see above import statement
hackernewsRss = HackerNewsRSS()

# Create a list of all the RSS Feed objects 
allFeeds:list[RSS_Feed] = [
    bleepingComputerRss,
    censysRss,
    censysDirRss,
    defenseDeptRss,
    microsoftRss,
    nvdRss,
    nistRss,
    #stateDeptRss,  # Intentionally commented out - see above import statement
    hackernewsRss
]
allArticles:list[RSS_Article] = []

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - # 
# Classifying the articles for each feed 
for feed in allFeeds: 
    #feed.classifyArticles(allTags, config['thread-limit']) 
    allArticles.extend(feed.articles)

"""
# Cluster analysis of articles
lda:LDA_Article_Clustering = LDA_Article_Clustering(allArticles, num_topics=20, limit=100)

with open('lda-test-assignments.txt', 'w') as file: 
    file.write(lda.strAllTopicAssignments())

s = ""
for i in range(len(lda.topics_dict.keys())):
    s += "\n" + lda.strInfoForTopic(i)

print(s)
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - # 
# Section for interacting with the remote DB



# The following block should only run if we have DB creds to access the remote DB. it can be skipped otherwise
if db_creds:              
    # Get all tags from the remote DB incase there are more than what we have locally
    allTags = dbConn.getAllTags()

    # Classify all the articles. This should run whether we are updating the remote db or just locally saving the data
    # --> This loop will check if we are updating the remote db and act accordingly
    for feed in allFeeds: 
        if not dbConn.addFeed(feed): 
            print(f"ERROR: There was an error adding the feed {feed} to the DB. Skipping the rest of this feed.")
            continue
        if dbConn.addArticles(feed.articles): print(f"\tSuccessfully added articles for {feed.feed_title}.")
        else: print(f"\tThere was some error adding the articles for {feed.feed_title}. Moving on.")
        
    # Success message
    print("[+] SUCCESS: All threads for classifying articles in feeds are complete.")


# NOTE: the time to save locally is trivial compared to the time to classify articles so no need for threading
if config['local-save']: 
    print("[+] NOTICE: Starting local saving for all feeds.")
    for feed in allFeeds: 
        feed.to_excel(config['local-save'], feed.feed_title.replace(" ", "_") + ".xlsx")
        feed.articleTagsToExcel(config['local-save'], feed.feed_title.replace(" ", "_") + "-articleTags.xlsx")

print("\nDONE. Check output for errors or more details.")
