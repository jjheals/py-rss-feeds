from FP_Classes.Set import Set
import os
import pandas as pd
from hashlib import sha1

# ------------------------------------------------------------------------------------------------- #
''' Tag - class for Tags '''
class Tag: 
    
    # Attributes 

    tagName:str
    tagDesc:str
    caseSensitive:bool
    count:int 
    
    ''' __init__(tagId, tagName, tagDesc) - Constructor '''
    def __init__(self, tagName:str, tagDesc:str, case:bool):
        self.tagName = tagName
        self.tagDesc = tagDesc
        self.caseSensitive = case
    

    
    ''' toString() - return this tag as a readable string
        :return a string representation of this tag
    '''
    def toString(self):
        return f"Tag Name: {self.tagName}\n\tTag Desc: {self.tagDesc}\n\tCase Sensitive: {self.caseSensitive}"
    
    ''' tagFromDict(dict) - create a Tag object from a dictionary object
        :param dict a dictionary object containing the info for this Tag
        :return a Tag object 
    '''
    @staticmethod 
    def tagFromDict(dict:dict[str,str]) -> object: return Tag(dict['tag_name'], dict['tag_desc'], dict['case_sensitive'])
    
# ------------------------------------------------------------------------------------------------- #
''' Tag_Set - a set of related tags '''
class Tag_Set(Set):
    
    tags_in_set:list[Tag] 
    
    def __init__(self, set_name:str, set_desc:str): 
        super().__init__(set_name, set_desc)
        self.tags_in_set = []
        
    ''' to_excel() - convert this Article_Set to an excel sheet containing the articles in this set 
        :param dataFolder path to the parent folder where we are saving data
        :param filePath path to the file within dataFolder to save this excel sheet
        :return False if error, True if success 
    '''
    def to_excel(self, dataFolder:str): 
        pathToFile = f"{dataFolder}/{self.set_name}-tagSet.xlsx"
        
        if not os.path.exists(dataFolder): 
            os.mkdir(dataFolder) 
            
        # Check if the file already exists
        try: existingDf = pd.read_excel(pathToFile)
        except FileNotFoundError: existingDf = pd.DataFrame()
        
        # Create the new dataframe
        columnNames = ['id', 'set_name', 'tag_name']
        
        dfList:list[list[str]] = []
        for t in self.tags_in_set: dfList.append([sha1(f"{self.set_name}{t.tagName}".encode()).hexdigest(), self.set_name, t.tagName])
        
        newDf:pd.DataFrame = pd.DataFrame(dfList, columns=columnNames)
        
        # Concat the existing DF and new DF
        combined:pd.DataFrame = pd.concat([existingDf, newDf], ignore_index=True)
        combined.drop_duplicates(inplace=True)
        
        try: combined.to_excel(pathToFile, index=False)
        except Exception as e: 
            print("ERROR in Tag_Set.to_excel(): there was an error writing to the excel file. Quitting.")
            print(e)
            return False