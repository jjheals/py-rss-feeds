
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article

'''
HackerNewsRSS(RSS_Feed) - a class designed specifically for the Hacker News RSS feed, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feed: https://hnrss.org/newest
        Feed title: Hacker News: Newest
        Feed Description: Hacker News RSS
    
'''
class HackerNewsRSS(RSS_Feed): 
    
    ''' HN_Article - nested class for Hacker News articles '''
    class HN_Article(RSS_Article): 

        HN_ArticleDiv:str = 'available-content'
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.HN_ArticleDiv, HackerNewsRSS.HN_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
                       
    # Attributes for HackerNewsRSS
    HN_FolderPath = "hackernews"
    HN_FeedLink:str = "https://hnrss.org/newest"
    HN_FeedTitle:str = "Hacker News"
    HN_FeedDesc:str = "Hacker News RSS"

    ''' HackerNewsRSS.__init__() - constructor for HackerNewsRSS
        NOTE: upon initialization, the class will automatically grab updated data from the RSS feed
    '''
    def __init__(self, seen_article_titles:list[str]=[]):
        super().__init__(self.HN_FolderPath, self.HN_FeedTitle, self.HN_FeedLink, self.HN_FeedDesc)
        self.__getFeedInfo__(seen_article_titles)
    
    ''' __getFeedInfo__() - get the info from this feed, including the attributes and articles
        :return void, save the result to this instance of RSS_Feed (self)
    '''
    def __getFeedInfo__(self, seen_article_titles:list[str]): 
        feed:fp.FeedParserDict = fp.parse(self.feed_link)
        
        for e in feed.entries: 
            if e.title in seen_article_titles: continue
            published:str = str(e.published).split("+")[0].rstrip()                         # Unique formatting of Hacker News published attribute
            self.articles.append(self.HN_Article(e.title, e.link, published, e.summary))
