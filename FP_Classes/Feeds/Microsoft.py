
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article

'''
MicrosoftRSS(RSS_Feed) - a class designed specifically for Microsoft's RSS feed, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feed: https://api.msrc.microsoft.com/update-guide/rss
        Feed title: MSRC Security Update Guide
        Feed Description:
    
    NOTE: MS_Article.MS_ArticleDiv is empty because these articles are primarily for CVE information only. Thus, the articles will be tagged with the CVE ID, but the articles do not
          contain more details, so it is a waste of time and resources to iterate through the content. 
          
'''
class MicrosoftRSS(RSS_Feed): 
    
    ''' MS_Article - nested class for MicrosoftRSS articles '''
    class MS_Article(RSS_Article): 

        MS_ArticleDiv:str = ''
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.MS_ArticleDiv, MicrosoftRSS.MS_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
                       
    # Attributes for CensysRSS
    MS_FolderPath = "microsoft"
    MS_FeedLink:str = "https://api.msrc.microsoft.com/update-guide/rss"
    MS_FeedTitle:str = "MSRC Security Update Guide"
    MS_FeedDesc:str = ""

    ''' MicrosoftRSS.__init__() - constructor for MicrosoftRSS
        NOTE: upon initialization, the class will automatically grab updated data from the RSS feed
    '''
    def __init__(self, seen_article_titles:list[str]=[]):
        super().__init__(self.MS_FolderPath, self.MS_FeedTitle, self.MS_FeedLink, self.MS_FeedDesc)
        self.__getFeedInfo__(seen_article_titles)
    
    ''' __getFeedInfo__() - get the info from this feed, including the attributes and articles
        :return void, save the result to this instance of RSS_Feed (self)
    '''
    def __getFeedInfo__(self, seen_article_titles:list[str]): 
        feed:fp.FeedParserDict = fp.parse(self.feed_link)

        if len(feed.entries) == 0: 
            print(f"NON-CRITICAL ERROR for feed \"{self.feed_title}\": No articles were found for this feed. It is possible this IP address is temporarily blocked. Skipping the rest of this feed.")
            return
        
        for e in feed.entries: 
            if e.title in seen_article_titles: continue
            self.articles.append(self.MS_Article(e.title, e.link, e.published, e.summary))
