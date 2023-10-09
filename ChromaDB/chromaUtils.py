from langchain.vectorstores import Chroma
from ChromaDB.client import persistent_client, embeddings

def getCollection(collection_name):
    langchain_chroma = Chroma(
        client=persistent_client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )
    return langchain_chroma

def clearCollection(list_of_collection_names):
    for collection_name in list_of_collection_names:
        try:
            persistent_client.delete_collection(name=collection_name)
        except:
            print(collection_name)

def createCollection(collection_name):
    persistent_client.get_or_create_collection(name=collection_name, embedding_function=embeddings)

def getDistinctFileNameList(collection_name):
    metadata_list = getCollection(collection_name).get()['metadatas']
    papers = [doc.get('fileName') for doc in metadata_list]
    return list(set(papers))