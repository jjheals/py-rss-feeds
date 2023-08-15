
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article

'''
StateDept_Counterterrorism(RSS_Feed) - a class designed specifically for the State Department's Counterterrorism RSS feed, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feed: https://www.state.gov/rss-feed/counterterrorism/feed/
        Feed title: Counterterrorism - United States Department of State
        Feed Description:  
    
'''
class StateDeptRSS(RSS_Feed): 
    
    ''' SDCT_Article - nested class for StateDept_CounterterrorismRSS articles '''
    class SDCT_Article(RSS_Article): 

        SDCT_ArticleDiv:str = 'entry-content'
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.SDCT_ArticleDiv, StateDeptRSS.SD_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
                       
    # Attributes for StateDept_DiplomaticSecurityRSS
    SD_FolderPath = "statedept"
    SD_Generic_FeedLink = "https://www.state.gov/rss-feeds/"
    SD_FeedLinks:list[str] = [
        "https://www.state.gov/rss-feed/counterterrorism/feed/",              # Counterterrorism
        #"https://www.state.gov/rss-feed/diplomatic-security/feed/",           # Diplomatic Security
        "https://www.state.gov/rss-feed/europe-and-eurasia/feed/",            # Europe and Eurasia
        "https://www.state.gov/rss-feed/east-asia-and-the-pacific/feed/",     # East Asia and the Pacific
        "https://www.state.gov/rss-feed/press-releases/feed/",                # Press Releases
        "https://www.state.gov/rss-feed/secretarys-remarks/feed/",            # Sectretary's Remarks
        "https://www.state.gov/rss-feed/western-hemisphere/feed/"             # Western Hemisphere
    ]
                              
    SD_FeedTitle:str = "United States Department of State"
    SD_FeedDesc:str = "Articles from the Dept. of State from various categories of interest"

    ''' StateDeptRSS.__init__() - constructor 
        NOTE: upon initialization, the class will automatically grab updated data from the RSS feed
    '''
    def __init__(self, seen_article_titles:list[str]=[]):
        super().__init__(self.SD_FolderPath, self.SD_FeedTitle, self.SD_Generic_FeedLink, self.SD_FeedDesc)
        self.__getFeedInfo__(seen_article_titles)
    
    ''' __getFeedInfo__() - get the info from this feed, including the attributes and articles
        :return void, save the result to this instance of RSS_Feed (self)
    '''
    def __getFeedInfo__(self, seen_article_titles:list[str]): 
        i=1
        for l in self.SD_FeedLinks:
            print(f"\tGetting articles for link {i}/{len(self.SD_FeedLinks)} | {l}")
            i+=1
            feed:fp.FeedParserDict = fp.parse(l)

            for e in feed.entries: 
                if e.title in seen_article_titles: continue
                desc = str(e.summary)[3:].split('<')[0]
                self.articles.append(self.SDCT_Article(e.title, e.link, e.published, desc))
