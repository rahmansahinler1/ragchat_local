import pandas as pd
import os


class DocumentationFunctions():
    def __init__(self,file_path = 'assets/performace_log.csv'):
        self.file_path = file_path
        pass
   
    def  performance_logger(self,dict):
        df = pd.DataFrame.from_dict([dict])
        if not os.path.isfile(self.file_path):
            df.to_csv(self.file_path,index=False)
        else:
            df.to_csv(self.file_path,mode='a',index=False,header=False)


        