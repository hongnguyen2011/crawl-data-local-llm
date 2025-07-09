"""
#     "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text.
#     "1. **Extract Information:** extract the information that directly matches the provided description: {parse_description}. "
# 2. "**No Extra Content:** Do not include any additional text, comments, or explanations in your response. 

"Please follow these instructions carefully: \n\n"
    "1. **Basic setting** you basic setting is to return most of the text content as long as it matches the provided description: {parse_description} "
    "2. We are specifically interested in the text that explain concepts, code explanations, the content of code blocks, and tables related to the topic. "
    "3. Dont return comments about the content or what you are about to do, if the information dont match the provided description, return all the content {dom_content} ."
"""


from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

template = (
    "You are tasked with structuring the information from the following text content: {dom_content}. return it in a structured format. "
)

model = OllamaLLM(model="llama3:latest")


def parse_with_ollama(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    parsed_results = []

    for i, chunk in enumerate(dom_chunks, start=1):
        response = chain.invoke(
            {"dom_content": chunk, "parse_description": parse_description}
        )
        print(f"Parsed batch: {i} of {len(dom_chunks)}")
        parsed_results.append(response)

    return "\n".join(parsed_results)
