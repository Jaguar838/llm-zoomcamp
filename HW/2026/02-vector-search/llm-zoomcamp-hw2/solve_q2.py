import numpy as np
from embedder import Embedder
from gitsource import GithubRepositoryDataReader

def main():
    # 1. Setup Embedder
    model_path = 'models/Xenova/all-MiniLM-L6-v2'
    embedder = Embedder(model_path)
    
    # 2. Get Query Vector (v) from Q1
    query = "How does approximate nearest neighbor search work?"
    v = embedder.encode(query)
    
    # 3. Fetch the specific document content
    # Note: We use the same commit and reader settings as in the notebook
    reader = GithubRepositoryDataReader(
        repo_owner="DataTalksClub",
        repo_name="llm-zoomcamp",
        commit_id="8c1834d",
        allowed_extensions={"md"},
        filename_filter=lambda path: "/lessons/" in path,
    )
    
    target_filename = '02-vector-search/lessons/07-sqlitesearch-vector.md'
    documents = [file.parse() for file in reader.read()]
    
    doc = next((d for d in documents if d['filename'] == target_filename), None)
    
    if doc is None:
        print(f"Document {target_filename} not found!")
        return
    
    # 4. Embed the document content
    v_doc = embedder.encode(doc['content'])
    
    # 5. Compute cosine similarity (dot product since vectors are normalized)
    similarity = v.dot(v_doc)
    
    print(f"Target file: {target_filename}")
    print(f"Similarity: {similarity:.2f}")

if __name__ == "__main__":
    main()
