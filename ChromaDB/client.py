from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import chromadb

# create embeddings here
model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
persistent_client = chromadb.PersistentClient(path='../db/')