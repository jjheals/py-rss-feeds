""" 
main.py

:author jhealey
    
FUNCTIONALITY: 

This script is designed to automatically pull the content from articles using public RSS feeds. Due to the differences among sites and their structures, each 
RSS feed must be explicitly defined in its own class (as a child of RSS_Feed). For example: BleepingComputerRSS is a child class of RSS_Feed, and BC_Article
is a child class of RSS_Article.

The script REQUIRES a remote database to store data. In the configuration file (see README for more details) there is the option to save the data locally in 
csv files, but local saving is an ADDITION not a SUBSTITUTION for the database. There are instructions on the database configuration in the README. 

To classify articles, the script uses keyword tagging with a NLM and predefined tags to identify common keywords among different articles. The database can then
be queried to find articles for a specific tag, feed, by title, etc., or any combination thereof. 

In the future, this script will use a different NLM to group articles in clusters based on their content. This will likely be done using LDA and similar 
clustering algorithms, and the database structure can handle this added functioanlity, but at this time (8/22/23) this script does not cluster similar articles
together by content. 

STEPS: 

The program is completely autonomous and does not require user interaction after runtime. It follows these steps in this order:

    0. Imports 
    
    1. Initializing variables - init all variables for configuration, the DB connection, local runtime storage, etc.
    
    2. Initialize all RSS feeds - initialize the RSS_Feed objects locally using the respective classes located in "FP_Classes/Feeds/". During this step, the 
                                  articles for each RSS feed are collected and their contents preprocessed and tagged using the predefined keywords/tags. The 
                                  script first reaches out to the DB to get a list of the article titles that we have already processed for this RSS feed to avoid
                                  wasting resources and time on duplicates. 

    3. Clustering analysis - Not yet completed. 
    
    4. Add data to the database - query the DB to add the new articles and their respective tags and clusters to the database to be referenced later.
    
    5. Local save - if configured, save the data locally in csv files (formatted and structured the same as the remote DB)
    
    
"""

# ------------------------------------------------------------------------------ #
# General imports 
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article
from FP_Classes.RSS_DB_Connection import RSS_DB_Connection
from FP_Classes.Tag import Tag
import json

# Imports for cluster analysis 
from data_analysis.ClusteringTechniques import *

# ------------------------------------------------------------------------------ #
# 0. All imports for all RSS feeds

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
# 1. Initialization of all variables

configDir = "config/"                # Change if you changed the default file hierarchy 
allArticles:list[RSS_Article] = []

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

if not dbConn.newTagsFromExcel(configDir + config['update-tags-filepath']): print("CRITICAL ERROR: There was an error adding tags to the DB. Moving on without updating remote DB.")
else: print("SUCCESS: DB tags updated successfully.")

# ------------------------------------------------------------------------------ #
# 2. Initialize all Feed objects 

# BleepingComputer
bc_seen_articles = dbConn.getAllArticleTitles(feedTitle=BleepingComputerRSS.BC_FeedTitle)
print(f"NOTICE: Initializing BleepingComputer - the DB currently already contains {len(bc_seen_articles)} BleepingComputer articles.")
bleepingComputerRss = BleepingComputerRSS(seen_article_titles=bc_seen_articles)

# Censys Global Reach
cens_seen_articles = dbConn.getAllArticleTitles(feedTitle=CensysRSS.CS_FeedTitle)
print(f"NOTICE: Initializing Censys Global Reach - the DB currently already contains {len(cens_seen_articles)} Censys Global Reach articles.")
censysRss = CensysRSS(seen_article_titles=cens_seen_articles)

# Censys Director Blog
censdir_seen_articles = dbConn.getAllArticleTitles(feedTitle=CensysDirRSS.CS_FeedTitle)
print(f"NOTICE: Initializing Censys Director Blog - the DB currently already contains {len(censdir_seen_articles)} Censys Director Blog articles.")
censysDirRss = CensysDirRSS(seen_article_titles=censdir_seen_articles)

# Department of Defense
dod_seen_articles = dbConn.getAllArticleTitles(feedTitle=DefenseDeptRSS.DoD_FeedTitle)
print(f"NOTICE: Initializing DOD RSS - the DB currently already contains {len(dod_seen_articles)} DOD RSS articles.")
defenseDeptRss = DefenseDeptRSS(seen_article_titles=dod_seen_articles)

# Microsoft 
ms_seen_articles = dbConn.getAllArticleTitles(feedTitle=MicrosoftRSS.MS_FeedTitle)
print(f"NOTICE: Initializing Microsoft RSS - the DB currently already contains {len(ms_seen_articles)} Microsoft RSS articles.")
microsoftRss = MicrosoftRSS(seen_article_titles=ms_seen_articles)

# National Vulnerability Database (NVD)
nvd_seen_articles = dbConn.getAllArticleTitles(feedTitle=NVD_RSS.NVD_FeedTitle)
print(f"NOTICE: Initializing NVD - the DB currently already contains {len(nvd_seen_articles)} NVD articles.")
nvdRss = NVD_RSS(seen_article_titles=nvd_seen_articles)

# National Institute of Science and Technology (NIST)
nist_seen_articles = dbConn.getAllArticleTitles(feedTitle=NIST_RSS.NIST_FeedTitle)
print(f"NOTICE: Initializing NIST - the DB currently already contains {len(nist_seen_articles)} NIST articles.")
nistRss = NIST_RSS(seen_article_titles=nist_seen_articles)

# State Department
sd_seen_articles = dbConn.getAllArticleTitles(feedTitle=StateDeptRSS.SD_FeedTitle)
print(f"NOTICE: Initializing State Dept - the DB currently already contains {len(sd_seen_articles)} State Dept articles.")
stateDeptRss = StateDeptRSS(seen_article_titles=sd_seen_articles)     

# Hacker News 
hn_seen_articles = dbConn.getAllArticleTitles(feedTitle=HackerNewsRSS.HN_FeedTitle)
print(f"NOTICE: Initializing Hacker News - the DB currently already contains {len(hn_seen_articles)} Hacker News articles.")
hackernewsRss = HackerNewsRSS(seen_article_titles=hn_seen_articles)

# Create a list of all the RSS Feed objects 
allFeeds:list[RSS_Feed] = [
    bleepingComputerRss,
    censysRss,
    censysDirRss,
    defenseDeptRss,
    microsoftRss,
    nvdRss,
    nistRss,
    stateDeptRss, 
    hackernewsRss
]

# ------------------------------------------------------------------------------ #
# 3. Clustering Analysis
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

# ------------------------------------------------------------------------------ #
# 4. Section for interacting with the remote DB
            
# Get all tags from the remote DB incase there are more than what we have locally
allTags = dbConn.getAllTags()

for feed in allFeeds: 
    
    # Check that this feed either exists in the DB or can be added 
    # to avoid issues with foreign key restraints
    if not dbConn.addFeed(feed): 
        print(f"ERROR: There was an error adding the feed {feed} to the DB. Skipping the rest of this feed.")
        continue
    
    # Add these articles to the running list of all articles
    allArticles.extend(feed.articles)

    # Try to add these articles to the DB
    if dbConn.addArticles(feed.articles): print(f"\tSuccessfully added articles for {feed.feed_title}.")
    else: print(f"\tThere was some error adding the articles for {feed.feed_title}. Moving on.")
    
# Success message
print("[+] SUCCESS: All threads for classifying articles in feeds are complete.")

# ------------------------------------------------------------------------------ #
# 5. Local save if configured 

# NOTE: the time to save locally is trivial compared to the time to classify articles so no need for threading
if config['local-save']: 
    print("[+] NOTICE: Starting local saving for all feeds.")
    for feed in allFeeds: 
        feed.to_excel(config['local-save'], feed.feed_title.replace(" ", "_") + ".csv")
        feed.articleTagsToCSV(config['local-save'], feed.feed_title.replace(" ", "_") + "-articleTags.csv")

print("\nDONE. Check output for errors or more details.")