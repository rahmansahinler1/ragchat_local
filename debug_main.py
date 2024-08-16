from app.application import App
from pipeline_setup.prefect_data_pipeline import FileDetectionFlow
from pipeline_setup.prefect_data_pipeline import FileDetector
from pipeline_setup.prefect_data_pipeline import FileProcessor
import re
import numpy as np
import faiss


detector = FileDetector()
detector.check_db_path()
changes, updated_memory_data = detector.check_changes()
if changes:
    processor = FileProcessor()
    # Read changed pdf files
    for change in changes:
        # Create embeddings
        sentences = processor.rf.read_pdf(pdf_path=change["file_path"])
        embeddings = processor.ef.create_vector_embeddings_from_sentences(sentences=sentences, batch_size=2000)

        # Detect changed domain
        pattern = r'domain\d+'
        match = re.search(pattern, change["file_path"])
        if match:
            domain = match[0]
            if domain in processor.change_dict.keys():
                processor.change_dict[domain]["sentences"].extend(sentences)
                processor.change_dict[domain]["embeddings"] = np.vstack((processor.change_dict[domain]["embeddings"], embeddings))
            else:
                processor.change_dict[domain] = {"sentences": sentences, "embeddings": embeddings}           
    # Update corresponding index
    for key, value in processor.change_dict.items():
        # Open corresponding index if already created, if not initialize one
        index_path = detector.db_folder_path / "indexes" / (key + ".pickle")
        try:
            index_object = processor.indf.load_index(index_path)
            index =  faiss.deserialize_index(index_object["index"])
            sentences = index_object["sentences"]

            # Append necessary parts to the index
            index.add(value["embeddings"])
            sentences.extend(value["sentences"])

            # Overwrite the index
            index_bytes = faiss.serialize_index(index=index)
            processor.indf.save_index(index_bytes=index_bytes, sentences=sentences, save_path=index_path)
        except FileNotFoundError:
            # Create the index
            index_bytes = processor.indf.create_index_bytes(embeddings=embeddings)
            processor.indf.save_index(index_bytes=index_bytes, sentences=sentences, save_path=index_path)

    # Update memory
    memory_json_path = detector.db_folder_path / "memory.json"
    processor.update_memory(memory_json_path=memory_json_path, memory_data=updated_memory_data)
