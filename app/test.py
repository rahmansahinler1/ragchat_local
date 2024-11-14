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
        test_dataset = load_dataset("aurelio-ai/ai-arxiv2-ragas-mixtral")
        self.processor = FileProcessor()
        self.test_dataset = test_dataset

    def search_index_with_test_questions(self):
        df = pd.DataFrame({
            "question": [],
            "contexts": [],
            "answer": [],
            "ground_truth": []
        })
        folder_path = Path("C:/Users/Nazm_/Documents/ragchat_local/db/test_docs")
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".pickle"):
                file_path = os.path.join(folder_path, file_name)
            index_object = self.index_dataset(file_path)
            text_index = self.processor.create_index(embeddings=index_object["embeddings"])
            sentences = index_object["sentences"]
            is_header = index_object["is_header"]
            is_table = index_object["is_table"]
            file_headers = index_object["file_header"]
            file_sentence_amount = index_object["file_sentence_amount"]                                   
            domain_name = file_name.split('.')[0]

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

                boost = self.search_index_header(query=original_query,dataset=is_header,sentences=sentences)
                boost_file_header = self.search_file_header_index(query=original_query,dataset=file_headers,sentences=sentences,file_sentece_amount=file_sentence_amount)
                boost_combined = 0.75 * boost + 0.25 * boost_file_header
                for query in processed_queries:
                    if(query=="\n" or query=="\n\n" or query=="no response" or query==""):
                        continue
                    else:
                        query_vector = self.processor.ef.create_vector_embedding_from_query(query=query)
                        D, I = text_index.search(query_vector, len(sentences))
                        for j, indexes in enumerate(I[0]):
                            if indexes in dict_resource:
                                dict_resource[indexes].append(D[0][j])
                            else:
                                dict_resource[indexes] = [D[0][j]]
                try:
                    avg_index_list = self.processor.avg_resources(dict_resource)
                    for key in avg_index_list:
                        avg_index_list[key] *= boost_combined[key]
                    sorted_dict = dict(sorted(avg_index_list.items(), key=lambda item: item[1]))
                    indexes = np.array(list(sorted_dict.keys()))
                    sorted_sentences = indexes[:10]
                    sorted_sentence_indexes = [(order, int(index)) for order, index in enumerate(sorted_sentences) if is_table[int(index)] == 0]
                    sorted_table_indexes = [(order, int(index)) for order, index in enumerate(sorted_sentences) if is_table[int(index)] == 1]
                except ValueError as e:
                    original_query = "Please provide meaningful query:"
                    print(f"{original_query, {e}}")

                for order,index in sorted_sentence_indexes:
                    if order == 0:
                        widen_sentences = self.widen_sentences(dataset = sentences, window_size=3, index=index)
                    elif order in range(1,4):
                        widen_sentences = self.widen_sentences(dataset = sentences, window_size=2, index=index)
                    else:
                        widen_sentences = self.widen_sentences(dataset = sentences, window_size=1, index=index)
                    all_widen_sentences.append(widen_sentences)

                if sorted_table_indexes:
                    table_context = self.processor.table_context_creator(index_list=sorted_table_indexes,dataset=is_table,sentences=sentences)
                    for tuple in table_context:
                        all_widen_sentences.insert(tuple[0],tuple[1])

                context = self.create_dynamic_context(sentences=all_widen_sentences)
                answer = self.processor.cf.response_generation(query=original_query, context=context)

                df = pd.concat([df, pd.DataFrame({
                    "question": question,
                    "answer": answer,
                    "contexts": [context.split('\n')],
                    "ground_truth": ground_truths
                })], ignore_index=True)

        return df

    def index_dataset(self, path):
        pickle_path = Path(path)
        if os.path.exists(pickle_path):
            try:
                index_object = self.processor.indf.load_index(index_path=pickle_path)
                if index_object is not None:
                    return index_object
            except FileNotFoundError as e:
                raise FileExistsError(f"Index file could not be opened!: {e}")
    
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
    
    def search_index_header(self, query, dataset, sentences):
        boost = np.ones(len(sentences))
        original_query = query.split('\n')[0]

        header_indexes = [index for index in range(len(dataset)) if dataset[index]]
        if header_indexes:
            headers = [sentences[header_index] for header_index in header_indexes]

            header_embeddings = self.processor.ef.create_vector_embeddings_from_sentences(sentences=headers)
            index_header = self.processor.create_index(embeddings=header_embeddings)

            D,I = index_header.search(self.processor.ef.create_vector_embedding_from_query(original_query),10)
            filtered_header_indexes = [header_index for index, header_index in enumerate(I[0]) if D[0][index] < 0.40]
            for i,filtered_index in enumerate(filtered_header_indexes):
                try:
                    start = header_indexes[filtered_index] + 1
                    end = header_indexes[filtered_index + 1]
                    if i == 0:
                        boost[start:end] *= 0.7
                    elif i in range(1,3):
                        boost[start:end] *= 0.8
                    else:
                        boost[start:end] *= 0.9
                except IndexError as e:
                    print(f"List is out of range {e}")
            return boost
        else:
            return boost
        
    def search_file_header_index(self, query, dataset, sentences, file_sentece_amount):
        boost = np.ones(len(sentences))
        original_query = query.split('\n')[0]
        if dataset:
            file_header_embeddings = self.processor.ef.create_vector_embeddings_from_sentences(dataset)
            file_header_index = self.processor.create_index(file_header_embeddings)

            D,I = file_header_index.search(self.processor.ef.create_vector_embedding_from_query(query=original_query),len(dataset))
            if sum(D[0])/len(D[0]) < 0.45:
                file_indexes = [file_index for index, file_index in enumerate(I[0]) if D[0][index] < sum(D[0])/len(D[0])]
            else:
                file_indexes = [file_index for index, file_index in enumerate(I[0]) if D[0][index] < 0.45]

            if file_indexes:
                for index in file_indexes:
                    try:
                        start = sum(sum(page_sentence_amount) for page_sentence_amount in file_sentece_amount[:index])
                        end = start + sum(file_sentece_amount[index])
                        boost[start:end] *= 0.9
                    except IndexError as e:
                        print(f"List is out of range {e}")
            return boost
        else:
            return boost
        
    def table_context_creator(self, index_list, dataset, sentences):
        table_clusters = []
        current_cluster = []
        text_pairs = []
        seen_clusters = set()

        for i, value in enumerate(dataset):
            if value == 1:
                current_cluster.append(i)
            elif current_cluster:
                table_clusters.append(current_cluster)
                current_cluster = []
    
        if current_cluster:
            table_clusters.append(current_cluster)
        
        for order, index in index_list:
            for cluster in table_clusters:
                if cluster[0] <= index <= cluster[-1]:
                    cluster_tuple = tuple(cluster)
                    if cluster_tuple not in seen_clusters:
                        seen_clusters.add(cluster_tuple)
                        text = ''.join(sentences[index] + '\n' for index in cluster)
                        text_pairs.append((order, text))
                        break
        return text_pairs


test_function = Test()
evaluation_df = test_function.search_index_with_test_questions()
result_df = test_function.evaluation(evaluation_df)
result_df.to_csv("db/test_docs/test_result.csv", index=False)
print(result_df)