
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article

'''
NIST_RSS(RSS_Feed) - a class designed specifically for the NIST's RSS feeds, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feed: https://www.nist.gov/news-events/cybersecurity/rss.xml
        Feed title: NIST - Cybersecurity/IT news and events
    
'''
class NIST_RSS(RSS_Feed): 
    
    ''' NIST_Article - nested class for NIST_RSS articles '''
    class NIST_Article(RSS_Article): 

        NIST_ArticleDiv:str = 'text-with-summary'
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.NIST_ArticleDiv, NIST_RSS.NIST_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
                       
    # Attributes for NVD_RSS
    NIST_FolderPath = "nist"
    NIST_Generic_FeedLink = "https://www.nist.gov/pao/nist-rss-feeds"
    NIST_FeedLinks:list[str] = [
                                "https://www.nist.gov/news-events/cybersecurity/rss.xml",
                                "https://www.nist.gov/news-events/information%20technology/rss.xml"
                            ]
    NIST_FeedTitle:str = "NIST Cybersecurity and IT news and events"
    NIST_FeedDesc:str = ""

    ''' NVD_RSS.__init__() - constructor for NVD_RSS
        NOTE: upon initialization, the class will automatically grab updated data from the RSS feed
    '''
    def __init__(self, seen_article_titles:list[str]=[]):
        super().__init__(self.NIST_FolderPath, self.NIST_FeedTitle, self.NIST_Generic_FeedLink, self.NIST_FeedDesc)
        self.__getFeedInfo__(seen_article_titles)
    
    ''' __getFeedInfo__() - get the info from this feed, including the attributes and articles
        :return void, save the result to this instance of RSS_Feed (self)
    '''
    def __getFeedInfo__(self, seen_article_titles:list[str]): 
        for l in self.NIST_FeedLinks: 
            feed:fp.FeedParserDict = fp.parse(l)

            for e in feed.entries: 
                if e.title in seen_article_titles: continue
                self.articles.append(self.NIST_Article(e.title, e.link, e.published, e.summary))
