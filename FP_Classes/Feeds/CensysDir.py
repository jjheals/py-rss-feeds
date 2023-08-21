
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article

'''
CensysNewsRSS(RSS_Feed) - a class designed specifically for the Censys News RSS feed, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feed: https://www.census.gov/content/census/en/newsroom/blogs/director.xml
        Feed title: Censys - Director Blog
        Feed Description:
    
'''
class CensysDirRSS(RSS_Feed): 
    
    ''' CS_Article - nested class for CensysRSS articles '''
    class CSDir_Article(RSS_Article): 

        CSDir_ArticleDiv:str = 'par parsys'
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.CSDir_ArticleDiv, CensysDirRSS.CS_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
                       
    # Attributes for BleepingComputerRSS
    CS_FolderPath = "censys"
    CS_FeedLink:str = "https://www.census.gov/content/census/en/newsroom/blogs/director.xml"
    CS_FeedTitle:str = "Censys Director Blog"
    CS_FeedDesc:str = ""

    ''' CensysDirRSS.__init__() - constructor for CensysDirRSS
        NOTE: upon initialization, the class will automatically grab updated data from the RSS feed
    '''
    def __init__(self, seen_article_titles:list[str]=[]):
        super().__init__(self.CS_FolderPath, self.CS_FeedTitle, self.CS_FeedLink, self.CS_FeedDesc)
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
            if e.title in seen_article_titles: 
                print(f"\tAlready seen {e.title}")
                continue
            self.articles.append(self.CSDir_Article(e.title, e.link, e.published, e.summary))
