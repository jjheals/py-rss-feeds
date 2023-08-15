
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article

'''
NVD_RSS(RSS_Feed) - a class designed specifically for the National Vulnerability Database's RSS feeds, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feed: https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml
        Feed title: National Vulnerability Database
        Feed Description: This feed contains the most recent CVE cyber vulnerabilities published within the National Vulnerability Database.
    
'''
class NVD_RSS(RSS_Feed): 
    
    ''' NVD_Article - nested class for NVD_RSS articles '''
    class NVD_Article(RSS_Article): 

        NVD_ArticleDiv:str = 'col-lg-9 col-md-7 col-sm-12'
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.NVD_ArticleDiv, NVD_RSS.NVD_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
                       
    # Attributes for NVD_RSS
    NVD_FolderPath = "nvd"
    NVD_FeedLink:str = "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml"
    NVD_FeedTitle:str = "National Vulnerability Database"
    NVD_FeedDesc:str = "This feed contains the most recent CVE cyber vulnerabilities published within the National Vulnerability Database."

    ''' NVD_RSS.__init__() - constructor for NVD_RSS
        NOTE: upon initialization, the class will automatically grab updated data from the RSS feed
    '''
    def __init__(self, seen_article_titles:list[str]=[]):
        super().__init__(self.NVD_FolderPath, self.NVD_FeedTitle, self.NVD_FeedLink, self.NVD_FeedDesc)
        self.__getFeedInfo__(seen_article_titles)
    
    ''' __getFeedInfo__() - get the info from this feed, including the attributes and articles
        :return void, save the result to this instance of RSS_Feed (self)
    '''
    def __getFeedInfo__(self, seen_article_titles:list[str]): 
        feed:fp.FeedParserDict = fp.parse(self.feed_link)

        for e in feed.entries: 
            if e.title in seen_article_titles: continue
            self.articles.append(self.NVD_Article(e.title, e.link, e.date, e.summary))
