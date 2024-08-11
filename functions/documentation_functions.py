import pandas as pd
import os


class DocumentationFunctions():
    """
    This function contains tools for performance tracking purposes.
    It uses pandas to keep the recordings on a csv file.
    """
    def __init__(self,file_path = 'db/kpi_tracking/performace_log.csv'):
        self.file_path = file_path
        pass
   
    def  performance_logger(self,dict):
        df = pd.DataFrame.from_dict([dict])
        if not os.path.isfile(self.file_path):
            df.to_csv(self.file_path,index=False)
        else:
                df_csv = pd.read_csv(self.file_path)
                df_combined = pd.concat([df,df_csv])
                df_combined = df_combined.drop_duplicates(subset = ['batch_size','sentence_amount'],keep="last").reset_index(drop=True)
                df_combined.to_csv(self.file_path,mode='w',index=False)


        