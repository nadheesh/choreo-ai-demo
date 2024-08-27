"""
Copyright (c) 2023, WSO2 LLC. (https://www.wso2.com/) All Rights Reserved.

WSO2 LLC. licenses this file to you under the Apache License,
Version 2.0 (the "License"); you may not use this file except
in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the
specific language governing permissions and limitations
under the License.
"""

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from langchain.chains import create_history_aware_retriever
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

# FastAPI app initialization
app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize Pinecone vector store
vector_store = PineconeVectorStore(embedding=embeddings)

# Initialize OpenAI language model
llm = ChatOpenAI(model_name="gpt-4o-mini")


# Pydantic models for request validation
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
    """
    Add data from a web page to the vector store.

    Args:
        request (AddDataRequest): The request containing the URL and user ID.

    Returns:
        dict: A message indicating success.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    try:
        loader = WebBaseLoader(request.url)
        docs = loader.load()  # avoid async loading due to nested async loop issue

        text_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.HTML,
            chunk_size=200,
            chunk_overlap=50
        )

        chunks = text_splitter.split_documents(docs)

        for chunk in chunks:
            chunk.metadata["user_id"] = request.user_id

        # need to improve not to add duplicates
        await vector_store.aadd_documents(chunks)

        return {"message": "Data added successfully"}
    except Exception as e:
        logger.error(f"Error adding data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/converse")
async def converse(request: ConversationRequest):
    """
    Process a conversation request and generate a response.

    Args:
        request (ConversationRequest): The conversation request details.

    Returns:
        dict: The AI-generated response.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    try:
        user_id = request.user_id
        message = request.message
        chat_history = [(msg.role, msg.content) for msg in request.chat_history]

        retriever = vector_store.as_retriever(
            search_kwargs={"filter": {"user_id": user_id}, "k": 5}
        )

        contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        qa_system_prompt = """You are an assistant for question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.
        
{context}"""
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        response = await rag_chain.ainvoke({"input": message, "chat_history": chat_history})
        return {"response": response['answer']}
    except Exception as e:
        logger.error(f"Error in conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
