"""
Script for creating a Faiss vector database from the api data retrieved.

Steps:
    - Loading parquet file from source
    - Creating Document(text+meta) for training
    - Create embedding with mistral
    - Create Faiss Index
    - Save vector store (index, meta, text) in destination
"""
import faiss
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS 
from langchain_mistralai import MistralAIEmbeddings
import logging
import os
import pathlib
import polars as pl
from typing import List, Dict, Optional
from uuid import uuid4

from rag_poc import config 

logger = logging.getLogger(__name__)

def build_index(
    source: pathlib.Path,
    destination: pathlib.Path,
    columns: List[str],
    id_column: Optional[str] = None
) -> None:
    """
    Building a FAISS for similarity search.
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Path {source} does not exist.")

    df: pl.DataFrame = pl.read_parquet(source)
    logger.debug("Dataframe shape: rows=%i, col=%i", df.shape[0], df.shape[1])

    if df.is_empty():
        raise ValueError("The Dataframe is empty")

    embeddings = MistralAIEmbeddings(
        api_key=config.load_api_key(),
        model="mistral-embed"     
    )

    index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))

    vector_store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )

    if id_column:
        ids: list = retrieve_id_column_from_df(df, id_column)
        if not len(ids) == len(set(ids)):
            logger.warning("The id_column from the dataframe contains duplicate ids.")
            logger.warning("number of ids: %i, number of unique ids: %i", len(ids), len(set(ids)))

        df: pl.DataFrame = df.drop(pl.col(id_column))
    else:
        ids: list = create_uuids(df.shape[0])

    documents: List[Document] = df_to_documents(df, columns) 
    logging.debug("len(documents)=%i", len(documents))

    vector_store.add_documents(documents=documents, ids=ids)
    logging.info("%i documents added to the vector store.", len(documents))

    vector_store.save_local(destination)
    logging.info("Vector store savec to '%s'.", destination)

def retrieve_id_column_from_df(df: pl.DataFrame, id_column: str) -> list[int]:
    if id_column not in df.columns:
        raise ValueError("ID column '%s' not in DataFrame." % id_column)
    return df.get_column(id_column).to_list()
    
def create_uuids(number: int) -> list[str]:
    return [str(uuid4()) for _ in range(number)]

def df_to_documents(df: pl.DataFrame, columns: list[str]) -> list[Document]:
    """
    Transform a polars DataFrame into a list of LangChain Documents,
    with page_content for the RAG and metadata.

    Parameters:
        df: The polars DataFrame.
        columns: The list of columns to add to the page_content of the Document.
    
    Raises:
        ValueError if the columns are not in the dataframe.
    """
    if not all(col in df.columns for col in columns):
        raise ValueError("Some columns are missing from the dataframe.")

    docs = df.to_dicts()
    documents = []

    for doc in docs:
        #adding 'columns' to the page_content
        text = "\n\n".join(filter(None, [doc.get(col) or "" for col in columns]))
        #creating metada excluding columns used for the page_content
        meta = {k:v for k, v in doc.items() if k not in columns}
        documents.append(Document(page_content=text, metadata=meta))

    return documents
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    build_index(
        source=config.DATA_FILE,        
        destination=config.VECTORS_FOLDER,
        columns=config.COLUMN_EMBEDDING,
        id_column=config.ID_COLUMN
    )

    logging.info("✅ Vector store saved.")
