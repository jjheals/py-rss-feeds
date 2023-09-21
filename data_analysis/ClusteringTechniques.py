
from FP_Classes.RSS_Feed import RSS_Article
from sklearn.feature_extraction.text import TfidfVectorizer 
from nltk.tokenize import word_tokenize
from random import randint
import numpy as np 


''' ArticleCluster


'''
class ArticleCluster: 
    
    pass


''' ArticleClusteringTechnique 


'''
class ArticleClusteringTechnique: 
    
    all_tokenized_contents:list[list[str]]
    all_contents:list[str]
    all_articles:list[RSS_Article]
    
    def __init__(self, articles:list[RSS_Article]):
        self.all_articles = articles 
        self.all_tokenized_contents = []
        self.all_contents = []
        self.__preprocessArticles__()

    # ------------------------------------------------------------------------------------------- # 
    ''' __preprocessArticles__() - preprocess all the given articles and save the respective contents
        and tokens in self.all_contents and self.all_tokenized_contents
        :return void
    '''
    def __preprocessArticles__(self):
        print("NOTICE: Preprocessing articles.")
        c=1
        num_articles = len(self.all_articles)
        for a in self.all_articles: 
            # Skip this article if it has not been classified/content not preprocessed
            
            print(f"\tProcessing article {c}/{num_articles}")
            theseTokens, thisContent = RSS_Article.__contentPreprocessing__(a.article_desc + " " + a.__getArticleContent__())
            self.all_contents.append(thisContent)
            self.all_tokenized_contents.append(theseTokens)
            c+=1
    

''' Gensim_Article_Clustering - perform gensim clustering analysis on a given list of articles

    :param list_of_articles a list of RSS_Article to perform clustering analysis on
    :param num_topics hyperparameter for the number of topics (clusters) - defaults to 10
    
    Methods: 
    
    __gensim__() ......... perform gensim clustering analysis
    __getTopicDict__() ... called by __gensim__(), saves the context of the corpus and LDA model results to self.topic_dict
    printTopicDict() ..... print self.topic_dict in meaningful format 
    
'''
import gensim
from gensim.models import LdaModel
from gensim.corpora import Dictionary 

class LDA_Article_Clustering(ArticleClusteringTechnique): 
    
    article_in_topics:dict[int, list]  # Dictionary of the topic assignments for articles of [key, value] -> [topic_id, list[(article_id, probability)]]
    num_topics:int                     # Given hyperparameter 
    topics_dict:dict                   # Dictionary of topic IDs and the topic objects
    limit:int                          # Limit on the number of articles out of the total given to consider
    
    # ------------------------------------------------------------------------------------------- # 
    def __init__(self, list_of_articles:list[RSS_Article], num_topics=10, limit=0):
        if limit: list_of_articles = list_of_articles[:limit]   # If given a limit, cut the number of articles
        super().__init__(list_of_articles)                      # Call super() for initialization
        self.num_topics = num_topics                            # Set the number of topics
        self.topics_dict = {}
        self.limit = limit
        
        # Init dict for articles in each topic so we can append to the list later
        self.article_in_topics = {}     
        for i in range(self.num_topics): self.article_in_topics[i] = []

        # Run the Gesim LDA Model
        self.__lda__()
    
    # ------------------------------------------------------------------------------------------- # 
    ''' __gensim__() - run gensim clustering algorithm and store the results in self.topic_dict
        :return void
    '''
    def __lda__(self) -> list: 
        print(f"[+] Performing LDA with num_topics = {self.num_topics} and limit = {self.limit}")
        dictionary = Dictionary(self.all_tokenized_contents)
        corpus = [dictionary.doc2bow(content) for content in self.all_tokenized_contents]

        lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=self.num_topics, passes=50)

        # Print the results
        for t_id, topic in lda_model.show_topics(num_topics=self.num_topics):
            self.topics_dict[t_id] = topic
            print(f"Topic: {topic} (id = {t_id})")       
    
        # Save the results in self.topic_dict
        self.__assignArticleTopics__(corpus, lda_model)
    
    # ------------------------------------------------------------------------------------------- # 
    ''' __assignArticleTopics__(corpus, lda_model) - convert the corpus and lda_model results to self.topic_dict
        :param corpus a valid corpus obj 
        :lda_model a valid trained LDA model 
        :return void
    '''
    def __assignArticleTopics__(self, corpus, lda_model:LdaModel):

        for article_id in range(len(corpus)):
            document_topics = lda_model.get_document_topics(corpus[article_id])
            sorted_topics = sorted(document_topics, key=lambda x: x[1], reverse=True)
            top_topic_id = sorted_topics[0][0]
            top_topic_prob = sorted_topics[0][1]
            
            self.article_in_topics[top_topic_id].append((article_id, top_topic_prob))
    
    # ------------------------------------------------------------------------------------------- # 
    ''' strAllTopicAssignments() - return self.article_in_topics dict in meaningful str format
        :return str
    '''
    def strAllTopicAssignments(self) -> str:
        s:str = ""
        for topic_id in self.article_in_topics: 
            s += f"\n\n-> Topic ID [{topic_id}] articles:"
            for t in self.article_in_topics[topic_id]: s += f"\n\tArticle ID: {t[0]}\t\tProb: {t[1]}"
        return s
    
    ''' strAInfoForTopic() - return self.topic_dict in meaningful str format
        :return str
    '''
    def strInfoForTopic(self, topic_id:int) -> str: 
        topic_info = self.topics_dict[topic_id]
        loa:list[RSS_Article] = []
        
        loa_ids:list[int] = [l[0] for l in self.article_in_topics[topic_id]]
        for id in loa_ids: loa.append(self.all_articles[id])
        
        s:str = ""
        s += f"\n\n[*] INFO FOR Topic ID: {topic_id}"
        s += f"\n\n[+] Details: {topic_info}\n\n"
        for a in loa: s += "\t" + a.toString()
        
        return s
    
''' KMeans_Article_Clustering 


'''
from sklearn.cluster import KMeans

class KMeans_Article_Clustering(ArticleClusteringTechnique): 
    
    k:int               # Number of clusters (topics)
    num_features:int
    cluster_labels:np.ndarray
    
    def __init__(self, list_of_articles:list[RSS_Article], k:int, num_features:int=1000): 
        super().__init__(list_of_articles)
        self.k = k
        self.num_features = num_features
        
        
    def __kMeans__(self): 
        tfidf_vectorizer = TfidfVectorizer(max_features=self.num_features)   # Init TF-IDF Vectorizer
        tfidf_matrix = tfidf_vectorizer.fit_transform(self.all_contents)

        # Perform K Means clustering (initial groupings)
        knn = KMeans(n_clusters=self.k, random_state=randint(0,100))
        self.cluster_labels:np.ndarray = knn.fit_predict(tfidf_matrix)
            