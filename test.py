import os
import json
from typing import List

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chat_models import ChatOpenAI

os.environ["OPENAI_API_KEY"] = "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"

model = ChatOpenAI(temperature=0)

class JokePunchLines(BaseModel):

    punchline:str = Field(description="answer to resolve the joke")
    reason:str = Field(description="reason of the answer")
# Define your desired data structure.
class Joke(BaseModel):
    setup: str = Field(description="question to set up a joke")
    # punchline: List[str] = Field(description="list of answers to resolve the joke")
    punchline: List['JokePunchLines']=Field(description="list of answers to resolve the joke")

class JokesList(BaseModel):
    jokes:List['Joke']=Field(description="list of jokes, atleast 3")
# And a query intented to prompt a language model to populate the data structure.
joke_query = "Tell me a joke."

# Set up a parser + inject instructions into the prompt template.
parser = JsonOutputParser(pydantic_object=JokesList)

prompt = PromptTemplate(
    template="Answer the user query.\n{format_instructions}\n{query}\n",
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = prompt | model | parser

response:JokesList=chain.invoke({"query": joke_query})
print(response)
print(response["jokes"][0])