from starter import rag

def main():
    print("Hello from 05-monitoring!")
    

    query = "How does the agentic loop keep calling the model until it stops?"
    answer = rag.rag(query)
    print(answer)


if __name__ == "__main__":
    main()
