"""
 Copyright (c) 2024, WSO2 LLC. (http://www.wso2.com). All Rights Reserved.

  This software is the property of WSO2 LLC. and its suppliers, if any.
  Dissemination of any information or reproduction of any material contained
  herein is strictly forbidden, unless permitted by WSO2 in accordance with
  the WSO2 Commercial License available at http://wso2.com/licenses.
  For specific language governing the permissions and limitations under
  this license, please see the license as well as any agreement you’ve
  entered into with WSO2 governing the purchase of this software and any
"""
import logging
import os
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import TokenTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

pinecone_index = os.environ.get("PINECONE_INDEX_NAME")
pinecone_api_key = os.environ.get("PINECONE_API_KEY")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to specify allowed origins, e.g., ["http://localhost:63342"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

logging.basicConfig(level=logging.DEBUG)

# Initialize the embedding function
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize the vector store
vector_store = PineconeVectorStore(index_name=pinecone_index, embedding=embeddings)

# Initialize the language model
llm = ChatOpenAI(model_name="gpt-4o-mini")

# Store conversation chains for each user
user_chains: Dict[str, ConversationalRetrievalChain] = {}


class AddDataRequest(BaseModel):
    url: str
    user_id: str


class Message(BaseModel):
    role: str
    content: Optional[str] = ""


class ConversationRequest(BaseModel):
    user_id: str
    message: str
    chat_history: List[Message]


@app.post("/add_data")
async def add_data(request: AddDataRequest):
    try:
        # Load the web page
        loader = WebBaseLoader(request.url)
        docs = loader.load()

        # Split the text into chunks
        text_splitter = TokenTextSplitter(
            encoding_name="cl100k_base",
            chunk_size=200,
            chunk_overlap=50
        )
        chunks = text_splitter.split_documents(docs)

        # Add metadata (user_id) to each chunk
        for chunk in chunks:
            chunk.metadata["user_id"] = request.user_id

        # Add the chunks to the vector store
        vector_store.add_documents(chunks)

        return {"message": "Data added successfully"}
    except Exception as e:
        raise e
        # raise HTTPException(status_code=500, detail=str(e))


@app.post("/converse")
async def converse(request: ConversationRequest):
    try:
        user_id = request.user_id
        message = request.message
        chat_history = [(msg.role, msg.content) for msg in request.chat_history]

        from langchain.chains import create_retrieval_chain
        from langchain.chains.combine_documents import create_stuff_documents_chain

        from langchain.chains import create_history_aware_retriever
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        # Create a retriever with user_id filter
        retriever = vector_store.as_retriever(
            search_kwargs={"filter": {"user_id": user_id}, "k": 3}
        )

        qa_system_prompt = """You are an assistant for question-answering tasks. \
        Use the following pieces of retrieved context to answer the question. \
        If you don't know the answer, just say that you don't know. \
        Use three sentences maximum and keep the answer concise.\

        {context}"""
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        # Run the conversation chain
        response = await rag_chain.ainvoke({"input": message, "chat_history": chat_history})
        return {
            "response": response['answer'],
        }
    except Exception as e:
        logging.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, port=8000)
