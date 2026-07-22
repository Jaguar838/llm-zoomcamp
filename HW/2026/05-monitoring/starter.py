from groq import Groq

from gitsource import GithubRepositoryDataReader
from minsearch import Index

from rag_helper import RAGTraced

from dotenv import load_dotenv
load_dotenv()

COMMIT = "8c1834d"

# --- Load the course lessons (same as HW1, HW2, HW4) ---
reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id=COMMIT,
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)
documents = [file.parse() for file in reader.read()]

index = Index(text_fields=["content"], keyword_fields=["filename"])
index.fit(documents)

client = Groq()
rag = RAGTraced(index=index, llm_client=client, model='llama-3.3-70b-versatile')

if __name__ == "__main__":
    query = "How does the agentic loop keep calling the model until it stops?"
    answer = rag.rag(query)
    print(answer)
