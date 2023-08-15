
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article
from FP_Classes.Tag import Tag
import requests 
from bs4 import BeautifulSoup 

'''
BleepingComputerRSS(RSS_Feed) - a class designed specifically for the BleepingComputer RSS feed, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feed: https://www.bleepingcomputer.com/feed/
        Feed title: BleepingComputer
        Feed Description: BleepingComputer - All Stories 
    
'''
class BleepingComputerRSS(RSS_Feed): 
    
    ''' BC_Article - nested class for BleepingComputer articles '''
    class BC_Article(RSS_Article): 

        BC_ArticleDiv:str = 'articleBody'
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.BC_ArticleDiv, BleepingComputerRSS.BC_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
            
            
    # Attributes for BleepingComputerRSS
    BC_FolderPath = "BleepingComputer"
    BC_FeedLink:str = "https://www.bleepingcomputer.com/feed/"
    BC_FeedTitle:str = "BleepingComputer"
    BC_FeedDesc:str = "BleepingComputer All Stories"

    ''' BleepingComputerRSS.__init__() - constructor for BleepingComputerRSS
        NOTE: upon initialization, the class will automatically grab updated data from the RSS feed
    '''
    def __init__(self, seen_article_titles:list[str]=[]):
        super().__init__(self.BC_FolderPath, self.BC_FeedTitle, self.BC_FeedLink, self.BC_FeedDesc)
        self.__getFeedInfo__(seen_article_titles)
    
    ''' __getFeedInfo__() - get the info from this feed, including the attributes and articles
        :return void, save the result to this instance of RSS_Feed (self)
    '''
    def __getFeedInfo__(self, seen_article_titles): 
        feed:fp.FeedParserDict = fp.parse(self.feed_link)
    
        if len(feed.entries) == 0: 
                print(f"NON-CRITICAL ERROR for feed \"{self.feed_title}\": No articles were found for this feed. It is possible this IP address is temporarily blocked. Skipping the rest of this feed.")
                return
        
        for e in feed.entries: 
            if e.title in seen_article_titles: continue
            self.articles.append(self.BC_Article(e.title, e.link, e.published, e.summary))

