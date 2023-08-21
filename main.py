
# General imports 
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article
from FP_Classes.RSS_DB_Connection import RSS_DB_Connection
from FP_Classes.Tag import Tag
import json
from threading import Thread 
import nltk 

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
nltk.download("wordnet")

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
bc_seen_articles = dbConn.getAllArticleTitles(feedTitle=BleepingComputerRSS.BC_FeedTitle)
print(f"NOTICE: Initializing BleepingComputer - the DB currently already contains {len(bc_seen_articles)} BleepingComputer articles.")
bleepingComputerRss = BleepingComputerRSS(seen_article_titles=bc_seen_articles)

cens_seen_articles = dbConn.getAllArticleTitles(feedTitle=CensysRSS.CS_FeedTitle)
print(f"NOTICE: Initializing Censys Global Reach - the DB currently already contains {len(cens_seen_articles)} Censys Global Reach articles.")
censysRss = CensysRSS(seen_article_titles=cens_seen_articles)

censdir_seen_articles = dbConn.getAllArticleTitles(feedTitle=CensysDirRSS.CS_FeedTitle)
print(f"NOTICE: Initializing Censys Director Blog - the DB currently already contains {len(censdir_seen_articles)} Censys Director Blog articles.")
censysDirRss = CensysDirRSS(seen_article_titles=censdir_seen_articles)

dod_seen_articles = dbConn.getAllArticleTitles(feedTitle=DefenseDeptRSS.DoD_FeedTitle)
print(f"NOTICE: Initializing DOD RSS - the DB currently already contains {len(dod_seen_articles)} DOD RSS articles.")
defenseDeptRss = DefenseDeptRSS(seen_article_titles=dod_seen_articles)

ms_seen_articles = dbConn.getAllArticleTitles(feedTitle=MicrosoftRSS.MS_FeedTitle)
print(f"NOTICE: Initializing Microsoft RSS - the DB currently already contains {len(ms_seen_articles)} Microsoft RSS articles.")
microsoftRss = MicrosoftRSS(seen_article_titles=ms_seen_articles)

nvd_seen_articles = dbConn.getAllArticleTitles(feedTitle=NVD_RSS.NVD_FeedTitle)
print(f"NOTICE: Initializing NVD - the DB currently already contains {len(nvd_seen_articles)} NVD articles.")
nvdRss = NVD_RSS(seen_article_titles=nvd_seen_articles)

nist_seen_articles = dbConn.getAllArticleTitles(feedTitle=NIST_RSS.NIST_FeedTitle)
print(f"NOTICE: Initializing NIST - the DB currently already contains {len(nist_seen_articles)} NIST articles.")
nistRss = NIST_RSS(seen_article_titles=nist_seen_articles)

sd_seen_articles = dbConn.getAllArticleTitles(feedTitle=StateDeptRSS.SD_FeedTitle)
print(f"NOTICE: Initializing State Dept - the DB currently already contains {len(sd_seen_articles)} State Dept articles.")
stateDeptRss = StateDeptRSS(seen_article_titles=sd_seen_articles)     

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
