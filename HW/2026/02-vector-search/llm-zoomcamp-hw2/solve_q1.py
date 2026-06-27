import numpy as np
from embedder import Embedder

def main():
    model_path = 'models/Xenova/all-MiniLM-L6-v2'
    embedder = Embedder(model_path)
    
    query = "How does approximate nearest neighbor search work?"
    v = embedder.encode(query)
    
    print(f"Vector length: {len(v)}")
    print(f"v[0] = {v[0]:.2f}")

if __name__ == "__main__":
    main()
