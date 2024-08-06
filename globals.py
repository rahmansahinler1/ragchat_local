from datetime import datetime
pdf_path = None
pdf_embeddings = None
pdf_sentences = []
index = None
sentence_number = None
total_emd_time = None
total_ind_time = None
batch_size = None
avg_emd_time = None
avg_ind_time = None

def update_kpi_dict():
    global kpi_dict
    kpi_dict = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "batch_size": batch_size,
        "sentence_amount": sentence_number,
        "total_emd_time": total_emd_time,
        "total_ind_time": total_ind_time,
        "avg_emd_time": avg_emd_time,
        "avg_ind_time": avg_ind_time
        }
