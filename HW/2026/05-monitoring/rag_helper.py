from opentelemetry import trace

tracer = trace.get_tracer("llm-zoomcamp")

INSTRUCTIONS = '''
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
'''

PROMPT_TEMPLATE = '''
QUESTION: {question}

CONTEXT:
{context}
'''.strip()


class RAGBase:

    def __init__(
        self,
        index,
        llm_client,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        course='llm-zoomcamp',
        model='llama-3.3-70b-versatile'
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.course = course
        self.prompt_template = prompt_template
        self.model = model

    def search(self, query, num_results=5):
        boost_dict = {'content': 1.0}

        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict
        )

    def build_context(self, search_results):
        lines = []

        for doc in search_results:
            lines.append(doc['content'])
            lines.append('')

        return '\n'.join(lines).strip()

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return self.prompt_template.format(
            question=query, context=context
        )

    def llm(self, prompt):
        input_messages = [
            {'role': 'system', 'content': self.instructions},
            {'role': 'user', 'content': prompt}
        ]

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=input_messages
        )

        return response.choices[0].message.content

    def rag(self, query):
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        return answer


class RAGTraced(RAGBase):

    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search") as span:
            span.set_attribute("query", query)
            results = super().search(query, num_results)
            span.set_attribute("num_results", len(results))
            return results

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            span.set_attribute("prompt", prompt)
            answer = super().llm(prompt)
            span.set_attribute("answer", answer)
            return answer

    def rag(self, query):
        with tracer.start_as_current_span("rag") as span:
            span.set_attribute("query", query)
            answer = super().rag(query)
            span.set_attribute("answer", answer)
            return answer
