from app.application import App
from pipeline_setup.data_pipeline import FileDetectionFlow
from pipeline_setup.data_pipeline import FileDetector
from pipeline_setup.data_pipeline import FileProcessor
import re
import numpy as np
import faiss

CREATE_DEPLOYMENT = False
DEBUG_PIPELINE = True
OPEN_GUI = False

if __name__ == "__main__":
    if OPEN_GUI:
        app = App()
        app.mainloop()

    if CREATE_DEPLOYMENT:
        detection_flow = FileDetectionFlow(interval=600)
        detection_flow.create_deployment()
    
    if DEBUG_PIPELINE:
        detector = FileDetector()
        detector.check_db_path()
        changes = detector.check_changes()
        if changes:
            processor = FileProcessor(changed_files=changes)
            # Read changed pdf files
            for change in changes:
                # Create embeddings
                sentences = processor.rf.read_pdf(pdf_path=change["file_path"])
                embeddings = processor.ef.create_vector_embeddings_from_sentences(sentences=sentences)

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
                    # Open corresponding index
                    index_path = detector.db_folder_path / "indexes" / (key + ".pickle")
                    index_object = processor.indf.load_index(index_path)
                    index =  faiss.deserialize_index(index_object["index"])
                    sentences = index_object["sentences"]

                    # Append necessary parts to the index
                    index.add(value["embeddings"])
                    sentences.extend(value["sentences"])

                    # Overwrite the index
                    index_bytes = faiss.serialize_index(index=index)
                    processor.indf.save_index(index_bytes=index_bytes, sentences=sentences, save_path=index_path)

# TODO: Add a logic if there is no domain for that file and create index for it
# TODO: Test the task and processing flow
