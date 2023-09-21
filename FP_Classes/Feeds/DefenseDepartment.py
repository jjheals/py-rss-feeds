
import feedparser as  fp
from FP_Classes.RSS_Feed import RSS_Feed, RSS_Article

'''
DefenseDeptRSS(RSS_Feed) - a class designed specifically for the Defense Department's RSS feeds, child class of FP_Classes.RSS_Feed

    The following are static attributes:
        Link to feeds list: https://www.defense.gov/news/rss/
    
'''
class DefenseDeptRSS(RSS_Feed): 
    
    ''' DoDArticle - nested class for DefenseDeptRSS articles '''
    class DoDArticle(RSS_Article): 

        DoD_ArticleDiv:str = 'content content-wrap'
        
        def __init__(self, articleTitle:str, articleLink:str, articlePubDate:str, articleDesc:str):
            super().__init__(self.DoD_ArticleDiv, DefenseDeptRSS.DoD_FeedTitle, articleTitle, articleLink, articlePubDate=articlePubDate, articleDesc=articleDesc)
                       
    # Attributes for StateDept_DiplomaticSecurityRSS
    DoD_FolderPath = "dod"
    DoD_Generic_FeedLink = "https://www.defense.gov/news/rss/"
    DoD_FeedLinks:list[str] = [
        "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=2&Site=945&max=10",    # Advisories
        "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=9&Site=945&max=10",    # Releases
        "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=800&Site=945&max=10",  # Featured Stories
    ]
                              
    DoD_FeedTitle:str = "Defense-gov Explore Feed"
    DoD_FeedDesc:str = "Stories from around the Department of Defense."

    ''' DefenseDeptRSS.__init__() - constructor 
        NOTE: upon initialization, the class will automatically grab updated data from the RSS feed
    '''
    def __init__(self, seen_article_titles:list[str]=[]):
        super().__init__(self.DoD_FolderPath, self.DoD_FeedTitle, self.DoD_Generic_FeedLink, self.DoD_FeedDesc)
        self.__getFeedInfo__(seen_article_titles)
    
    ''' __getFeedInfo__() - get the info from this feed, including the attributes and articles
        :return void, save the result to this instance of RSS_Feed (self)
    '''
    def __getFeedInfo__(self, seen_article_titles): 
        i=1
        for l in self.DoD_FeedLinks:
            print(f"\tGetting articles for link {i}/{len(self.DoD_FeedLinks)} | {l}")
            i+=1
            feed:fp.FeedParserDict = fp.parse(l)
            
            if len(feed.entries) == 0: 
                print(f"\tNON-CRITICAL ERROR for feed \"{self.feed_title}\": No articles were found for this feed. It is possible this IP address is temporarily blocked. Skipping the rest of this feed.")
                return
        
            for e in feed.entries: 
                if e.title in seen_article_titles: 
                    print(f"seen title {e.title}")
                    continue
                desc = str(e.summary)[3:].split('<')[0]
                try: self.articles.append(self.DoDArticle(e.title, e.link, e.published, desc))
                except: continue