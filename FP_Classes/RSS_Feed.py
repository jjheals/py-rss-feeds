
import feedparser as  fp
import pandas as pd
from FP_Classes.Tag import Tag
import requests 
from hashlib import sha1
import os
from bs4 import BeautifulSoup
from threading import Thread
from time import sleep
from FP_Classes.Set import Set
import datetime as dt 
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re

# ------------------------------------------------------------------------------------------------- #
''' RSS_Article - generic class for RSS articles. Each RSS Feed has its own class and nested 
                  Articles class that is more customized to that RSS Feed, but this class 
                  provides a way to more generically specify articles once they've been processed
'''
class RSS_Article: 
    
    articleDiv:str          # The div in the actual article for this RSS Feed that contains the article body. Varies by feed/site
    feed_title:str          # Title of the RSS feed
    article_title:str       # Title of this article
    article_link:str        # Link to this article
    pub_date:str            # Published date of this article
    article_desc:str        # Description/summary of this article
    tags:list[str]          # A list of tag names associated with this article
    
    raw_content:str           # Content of this article before any preprocessing - exactly as pulled from site
    preprocessed_content:str  # Content of this article after preprocessing - stripped down to key words for analysis
    article_tokens:list[str]  # List of tokens for the content of this article (preprocessed_content as a list)
    
    ''' __init__(articleDiv, feedTitle, articleTitle, articleLink, articlePubDate, articleDesc) - Constructor
        :param articleDiv:str
        :param feedTitle:str
        :param articleTitle:str 
        :param articleLink:str 
        :param articlePubDate:str
        :param articleDesc:str
    '''
    def __init__(self, articleDiv:str, feedTitle:str, articleTitle:str, articleLink:str, articlePubDate:str="", articleDesc:str="", process:bool=True):
        print(f"[+] INIT article \"{feedTitle} - {articleTitle}\"")
        self.articleDiv = articleDiv
        self.feed_title = feedTitle
        self.article_title = articleTitle
        self.article_link = articleLink
        self.pub_date = RSS_Article.__standardizeDate__(articlePubDate)
        self.article_desc = articleDesc
        self.tags = []
        
        # If we are processing this article (getting and preprocessing the content)
        if process:
            # If a div is specified, then get the content. Otherwise the content is not relevant (see Microsoft's implementation for an example)
            print(f"\t[+] Getting article content...")
            if self.articleDiv: self.raw_content = self.__getArticleContent__()
            else: self.raw_content = ""
            
            # Preprocess the content
            print(f"\t[+] Preprocessing content...\n")
            self.article_tokens, self.preprocessed_content = RSS_Article.__contentPreprocessing__(self.raw_content)
            
            # Sanitize the article's text fields to avoid any future issues with special characters 
            self.sanitize()
        
    ''' classify(tags) - assign tags to this article based on the title
        :param tags a list of tag objects that we are interested in 
        : return void but add the relevant tags to this instance of article
        
        NOTE: Tags can be case sensitive. This is because tags can also be more than one word, thus splitting the article title/desc by " " is not
              going to work. Allowing tags to be case sensitive mitigates false positives by finding, for example "AI" in the word "against" and 
              similar issues. 
    '''
    def classify(self, tags:list[Tag]) -> None: 
        
        # RULE BASED TAGGING 
        tagstr:str = "|".join([t.tagName for t in tags])                    # For the regex expression
        tagPattern:re.Pattern = re.compile(r'\b(' + fr'{tagstr}' + r')\b')  # Create the regex pattern

        # Search this article's raw content and assign tags found 
        if tagPattern.search(self.raw_content): self.tags = list(set(tagPattern.findall(self.raw_content)))

    
    ''' __getArticleContent__() - get the content for this article from the site (requires self.articleDiv be valid)
        :return this articles content as a string
    '''        
    def __getArticleContent__(self) -> str:
        try:
            headers = { 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'              
            }
            
            # Fetch the HTML content
            response = requests.get(self.article_link, headers=headers)
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find and extract the article content
            # We will inspect the HTML structure of the specific article to find the relevant tags
            article_content = soup.find('div', class_=self.articleDiv)
            
            return article_content.get_text() if article_content else "Content not found."
            
        except requests.exceptions.RequestException as e:
            return f"Error fetching the article: {e}"
        except Exception as e:
            return f"Error: {e}"
    
    ''' toList() - return this article in a meaningful list format
        :return list
    '''        
    def toList(self) -> list: return [self.feed_title, self.article_title, self.article_link, self.pub_date, self.article_desc]
    
    ''' toString() - return this article as a meaningful string 
        :return str
    '''
    def toString(self) -> str:
        s = f"{self.feed_title}: {self.article_title}\n"
        s += f"\t\tLink: {self.article_link}\n"
        s += f"\t\tPublish Date: {self.pub_date}\n"
        s += f"\t\tDescription: {self.article_desc}\n"
        return s
    
    ''' sanitize() - replace the invalid characters in this article's title, description, and content
        :return void
    '''
    def sanitize(self) -> None:
        self.article_title = self.article_title.replace("\"", "")
        self.article_desc = self.article_desc.replace("\"", "")
        self.raw_content = self.raw_content.replace('"', "")
        self.raw_content = self.raw_content.replace("'", "")
        self.raw_content = self.raw_content.replace("\\", "")
        
    ''' __standardizeDate(dateStr) - convert the given date string into a standard format (YYYY-MM-DD)
        :param dateStr:str string representation of a date in arbitrary format 
        :return str of the standardized date
    '''
    @staticmethod
    def __standardizeDate__(dateStr):
        input_formats = ["%Y-%m-%d %H:%M:%S", 
                         "%m/%d/%Y", "%b %d, %Y",    
                         "%a, %d %b %Y %H:%M:%S %z", # BleepingComputer, NIST
                         "%a, %d %b %Y %H:%M:%S %Z", # Microsoft, DoD
                         "%a, %d %b %Y %H:%M:%S",    # HackerNews
                         "%Y-%m-%dT%H:%M:%SZ"        # NVD
                         ]
        output_format = "%Y-%m-%d"

        for input_format in input_formats:
            try:
                # Try to parse the date string using each input format
                date_obj = dt.datetime.strptime(dateStr, input_format)
                # If successful, format the date in the desired output format
                standardized_date = date_obj.strftime(output_format)
                return standardized_date
            except ValueError:
                pass
        # Return None if none of the input formats match
        return dateStr
    

    ''' __contentPreprocessing__(text) - preprocess the given block of text to format it for analysis 
        :param text a string of the text to process
        :return the pre-processed block of text 
        
        STEPS: 
            1. Tokenization - Separating the text into meaningful chunks 
            2. Remove stop words - remove words that have little or no meaning in the english language ("the", "a", "and", "in", etc)
            3. Lemmatization - Standardize the verb/noun tenses to their base meanings (running -> run, bicycles -> bicycle, etc)
        
        # NOTE: run "nltk.download('wordnet') if this is the first ever time running
        
    '''
    @staticmethod
    def __contentPreprocessing__(text:str):
        text = re.sub(r'\\', '', text)
        
        # Install the required packages from NLTK if needed 
        try: nltk.corpus.wordnet
        except LookupError: nltk.download('wordnet')
        
        try: nltk.data.find('tokenizers/punkt') 
        except LookupError: nltk.download('punkt')
        
        try: nltk.corpus.stopwords.words('english')
        except LookupError: nltk.download('stopwords') 
        
        # Tokenization 
        tokens = word_tokenize(text)                                        # Split the text into meaningful chunks/tokens
        tokens = [token.lower() for token in tokens if token.isalpha()]     # Perform tokenization on the list of tokens
        
        # Stop words
        stop_words = set(stopwords.words('english'))                        # Get a set of stop words to remove (the, a, an, and, in, ...)
        tokens = [token for token in tokens if token not in stop_words]     # Remove stop words from the list of tokens 
        
        # Lemmatization 
        lemmatizer = WordNetLemmatizer()                                    # Init lemmatizer 
        tokens = [lemmatizer.lemmatize(token) for token in tokens]           # Perform lemmatization on the list of tokens
        
        # Join the list of tokens back as a single string and return 
        return tokens, " ".join(tokens)

# ------------------------------------------------------------------------------------------------- #
''' RSS_Feed - generic class for RSS_feeds '''
class RSS_Feed: 

    # Attributes for RSS_Feed
    folderPath:str
    feed_title:str
    feed_link:str
    feed_desc:str 
    articles:list[RSS_Article]
    
    def __init__(self, folderPath:str, feedTitle:str, feedLink:str, feedDesc:str): 
        print(f"[+] Initializing feed: {feedTitle} | {feedLink}")
        
        self.folderPath = folderPath
        self.feed_title = feedTitle
        self.feed_link = feedLink
        self.feed_desc = feedDesc
        self.articles = []
            
    ''' to_excel(pathToFile) - save this RSS_Feed instance to an excel file at the given path
        :param pathToFile - path to the excel file to save the RSS_Feed
        :return void, save the excel file at the given path
        
        NOTE: if the specified path exists, then this RSS_Feed instance will be appended to the 
              existing data. If the file does not exist, then the file will be created. Note that 
              if the file does exist, it must have the same number and names of the columns as
              specified in this function or the program will throw an error. 
    '''
    def to_excel(self, dataFolder:str, pathToFile:str):
        pathToFile = dataFolder + self.folderPath + "/" + pathToFile
        
        if not os.path.exists(dataFolder + self.folderPath): 
            os.mkdir(dataFolder + self.folderPath) 
            
        # Check if the file already exists
        try: existingDf = pd.read_excel(pathToFile)
        except FileNotFoundError: existingDf = pd.DataFrame()
        
        # Create the new dataframe
        columnNames = ['Feed_Name', 'Article_Name', 'Article_Link', 'Article_Pub_Date', 'Article_Desc']
        
        dfList:list[list[str]] = []
        for a in self.articles: dfList.append(a.toList())
        
        newDf:pd.DataFrame = pd.DataFrame(dfList, columns=columnNames)
        
        # Concat the existing DF and new DF
        combined:pd.DataFrame = pd.concat([existingDf, newDf], ignore_index=True)
        combined.drop_duplicates(inplace=True)
        
        try: combined.to_excel(pathToFile, index=False)
        except Exception as e: 
            print("ERROR in RSS_Feed.to_excel(): there was an error writing to the excel file. Quitting.")
            print(e)
            return False
        
    
    ''' classifyTitles(tags) - assign tags to this feed's articles based on the titles 
        :param tags a list of Tag objects 
        :return void
    '''
    def classifyArticles(self, tags:list[Tag], limit=0):
        print(f"[+] Classifying all articles for {self.feed_title} | number of articles: {len(self.articles)}")
        
        c=1
        for a in self.articles: 
            if limit and c >= limit: break
            print(f"\tClassifying article {c}/{len(self.articles)}") 
            a.classify(tags)
            c+=1
        print(f"\nNOTICE: Done classifying articles for {self.feed_title}. Exiting.")
        
    ''' articleTagsToExcel(pathToFile) - create an excel sheet for this feed's articles and their associated tags
        :param pathToFile path to the excel file to save the results
        :return False if error, True if success
    '''
    def articleTagsToExcel(self, dataFolder:str, pathToFile:str) -> bool:
        pathToFile = dataFolder + self.folderPath + "/" + pathToFile
        
        # Check that the path to the directory exists, create it if not
        if not os.path.exists(dataFolder + self.folderPath): 
            os.mkdir(dataFolder + self.folderPath) 
        
        # Check if this is a valid file name (must be excel/xlsx)
        if pathToFile[-5:] != ".xlsx": 
            print(f"ERROR in RSS_Feed.articleTagsToExcel(): \"{pathToFile}\" is not a valid excel file name. Quitting.")
            return
        
        # If the file already exists, then get the data currently there
        try: existingDf = pd.read_excel(pathToFile)
        except FileNotFoundError: existingDf = pd.DataFrame()

        # Column headers
        columns = ['id', 'article_title', 'tag_name']
        
        # List of instances (rows) for the dataframe
        loi:list = []
        for a in self.articles: 
            for t in a.tags:
                loi.append([sha1(f'{a.article_title}{t}'.encode()).hexdigest(), a.article_title, t])
                
        df = pd.DataFrame(loi, columns=columns)                     # Create the dataframe
        df.reset_index(drop=True)                                   # Drop the index column
        combined = pd.concat([existingDf, df], ignore_index=True)   # Combine the new DF with the existing data
        combined.drop_duplicates(inplace=True, keep='last')         # Drop duplicates while keeping the most recent copy
        
        # Write to the excel file
        try: combined.to_excel(pathToFile, index=False)
        except Exception as e: 
            print("ERROR in RSS_Feed.articleTagsToExcel(): there was an error writing to the excel file. Quitting.")
            print(e)
            return False
        
        return True
        
        
        
# ------------------------------------------------------------------------------------------------- # 
''' ARTICLE_SET - a set of related articles '''
class Article_Set(Set): 

    articles_in_set:list[RSS_Article]
    
    def __init__(self, set_name:str, set_desc:str=""):
        super().__init__(set_name, set_desc)
        self.articles_in_set = []
        
    ''' to_excel() - convert this Article_Set to an excel sheet containing the articles in this set 
        :param dataFolder path to the parent folder where we are saving data
        :param filePath path to the file within dataFolder to save this excel sheet
        :return False if error, True if success 
    '''
    def to_excel(self, dataFolder:str): 
        pathToFile = f"{dataFolder}/{self.set_name.replace(' ', '_')}-articleSet.xlsx"
        
        if not os.path.exists(dataFolder): 
            os.mkdir(dataFolder) 
            
        # Check if the file already exists
        try: existingDf = pd.read_excel(pathToFile)
        except FileNotFoundError: existingDf = pd.DataFrame()
        
        # Create the new dataframe
        columnNames = ['id', 'set_name', 'article_title']
        
        dfList:list[list[str]] = []
        for a in self.articles_in_set: dfList.append([sha1(f"{self.set_name}{a.article_title}".encode()).hexdigest(), self.set_name, a.article_title])
        
        newDf:pd.DataFrame = pd.DataFrame(dfList, columns=columnNames)
        
        # Concat the existing DF and new DF
        combined:pd.DataFrame = pd.concat([existingDf, newDf], ignore_index=True)
        combined.drop_duplicates(inplace=True)
        
        try: combined.to_excel(pathToFile, index=False)
        except Exception as e: 
            print("ERROR in Article_Set.to_excel(): there was an error writing to the excel file. Quitting.")
            print(e)
            return False