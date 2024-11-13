from ragas.metrics import AnswerRelevancy, Faithfulness, ContextPrecision, ContextRecall
from ragas import evaluate
from datasets import load_dataset, Dataset
import sys
sys.path.append('.')
from app.data_pipeline import FileProcessor
import pandas as pd
import numpy as np
from tqdm.auto import tqdm
from pathlib import Path
import os

class Test():
    def __init__(self):
        document_dataset = load_dataset("jamescalam/ai-arxiv2-semantic-chunks", split="train[:10]")
        test_dataset = load_dataset("aurelio-ai/ai-arxiv2-ragas-mixtral")
        self.processor = FileProcessor()
        self.dataset = document_dataset
        self.test_dataset = test_dataset

    def search_index_with_test_questions(self):
        df = pd.DataFrame({
            "question": [],
            "contexts": [],
            "answer": [],
            "ground_truth": []
        })
        test_index = self.index_dataset()
        for row in tqdm(self.test_dataset['train']):
            all_widen_sentences = []
            dict_resource = {}
            new_queries = self.processor.generate_additional_queries(query=row["question"])
            question = row["question"]
            ground_truths = row["ground_truth"]
            if new_queries[0][0] == "[":
                processed_queries = self.processor.query_preprocessing(new_queries)
                original_query = processed_queries[0]
            else:
                processed_queries = new_queries.split("\n")
                processed_queries = processed_queries[:6]
                original_query = processed_queries[0]

            for i,query in enumerate(processed_queries):
                if(query=="\n" or query=="\n\n" or query=="no response" or query==""):
                    continue
                else:
                    query_vector = self.processor.ef.create_vector_embedding_from_query(query=query)
                    D, I = test_index.search(query_vector, 5)
                    for j, indexes in enumerate(I[0]):
                        if indexes in dict_resource:
                            if not isinstance(dict_resource[indexes], list):
                                dict_resource[indexes] = [dict_resource[indexes]]
                            dict_resource[indexes].append(float(D[0][j]))
                        else:
                            dict_resource[indexes] = [float(D[0][j])]
            try:
                avg_index_list = self.processor.avg_resources(dict_resource)
                sorted_dict = dict(sorted(avg_index_list.items(), key=lambda item: item[1]))
                indexes = np.array(list(sorted_dict.keys()))
                sorted_sentences = indexes[:10]
            except ValueError as e:
                original_query = "Please provide meaningful query:"
                print(f"{original_query, {e}}")

            for order,index in enumerate(sorted_sentences):
                if order == 0:
                    widen_sentences = self.widen_sentences(dataset=self.dataset['content'], window_size=3, index=index)
                elif order in range(1,4):
                    widen_sentences = self.widen_sentences(dataset=self.dataset['content'], window_size=2, index=index)
                else:
                    widen_sentences = self.widen_sentences(dataset=self.dataset['content'], window_size=1, index=index)
                all_widen_sentences.append(widen_sentences)

            context = self.create_dynamic_context(sentences=all_widen_sentences)
            answer = self.processor.cf.response_generation(query=original_query, context=context)

            df = pd.concat([df, pd.DataFrame({
                "question": question,
                "answer": answer,
                "contexts": [context.split('\n')],
                "ground_truth": ground_truths
            })], ignore_index=True)

        return df

    def index_dataset(self):
        pickle_path = Path("C:/Users/Nazm_/Documents/ragchat_local/db/test_docs/test_pickle.pickle")
        if os.path.exists(pickle_path):
            try:
                index_object = self.processor.indf.load_index(index_path=pickle_path)
                if index_object is not None:
                    return index_object
            except FileNotFoundError as e:
                raise FileExistsError(f"Index file could not be opened!: {e}")
        else:
            embeddings = self.processor.ef.create_vector_embeddings_from_sentences(self.dataset['content'])
            dataset_index = self.processor.create_index(embeddings=embeddings)
            self.processor.indf.save_index(index_object=dataset_index, save_path=pickle_path)
            return dataset_index
    
    def widen_sentences(self, dataset: list, window_size: int, index: int):  
        text = ""
        start = max(0, index - window_size)
        end = min(len(dataset) - 1, index + window_size)
        for i in range(start, end+1):
            text += dataset[i]
        return text
    
    def evaluation(self, dataframe):
        eval_data = Dataset.from_dict(dataframe)
        result = evaluate(
            dataset=eval_data,
            metrics=[
                AnswerRelevancy(),
                Faithfulness(),
                ContextPrecision(),
                ContextRecall()
            ],
        )
        result = result.to_pandas()
        return result
    
    def create_dynamic_context(self, sentences):
        context = ""
        for sentence in sentences:
            context += f"{sentence}\n"
        return context

test_function = Test()
evaluation_df = test_function.search_index_with_test_questions()
result_df = test_function.evaluation(evaluation_df)
result_df.to_csv("C:/Users/Nazm_/Documents/ragchat_local/test_result.csv", index=False)
print(result_df)