
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article

'''
CensysRSS(RSS_Feed) - a class designed specifically for the Censys Global Reach Blog RSS feed, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feed: https://www.census.gov/content/census/en/newsroom/blogs/global-reach.xml
        Feed title: Censys - Global Reach
        Feed Description:
    
'''
class CensysRSS(RSS_Feed): 
    
    ''' CS_Article - nested class for CensysRSS articles '''
    class CS_Article(RSS_Article): 

        CS_ArticleDiv:str = 'par parsys'
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.CS_ArticleDiv, CensysRSS.CS_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
                       
    # Attributes for CensysRSS
    CS_FolderPath = "censys"
    CS_FeedLink:str = "https://www.census.gov/content/census/en/newsroom/blogs/global-reach.xml"
    CS_FeedTitle:str = "Censys Global Reach"
    CS_FeedDesc:str = ""

    ''' CensysRSS.__init__() - constructor for CensysNewsRSS
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
                print(f"seen title {e.title}")
                continue
            try: self.articles.append(self.CS_Article(e.title, e.link, e.published, e.summary))
            except: continue
