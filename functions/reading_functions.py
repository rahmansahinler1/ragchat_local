from langchain_community.document_loaders import PyPDFLoader


class ReadingFunctions:
    def __init__(self):
        pass

    def read_pdf(self, path: str):
        """
        The code is responsible for reading a PDF file and splitting it into individual pages.
        """
        loader = PyPDFLoader(path)
        pages = loader.load_and_split()
        return pages
