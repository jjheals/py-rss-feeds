
''' Set - generic class for Article_Set and Tag_Set to implement common functionalities '''
class Set: 
    
    set_name:str
    set_desc:str
    
    def __init__(self, set_name:str, set_desc:str):
        self.set_name = set_name
        self.set_desc = set_desc
    