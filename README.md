Here's the updated `README.md` with a section about setting environment variables:

---

# Chat Agent with PDF Knowledge Base

This repository contains the code for a chat agent capable of answering questions by referring to PDF documents uploaded by users. The agent is designed to continuously learn from the provided documents, offering a personalized experience tailored to each user. Users can upload PDFs to teach the agent, and then ask questions based on the content of those documents.

### Example Interaction
- **User:** Uploads a document about cities.
- **Question:** What is the capital of the USA?
- **Agent:** The capital of the USA is Washington, D.C.
- **Question:** What is the population there?
- **Agent:** As of 2021, the population of Washington, D.C. is approximately 670,000.

## Building the Chat Agent Service

The service consists of two main components:

### 1. PDF Processing and Storage Endpoint
This endpoint allows users to upload PDF documents. The service processes these documents, extracting the text and breaking it down into manageable chunks. The processed data is then stored in a vector database, indexed by user ID, enabling personalized retrieval of information later.

### 2. Question Answering Endpoint
This endpoint enables users to ask questions based on the content of the uploaded PDFs. It uses a Retrieval Augmented Generation (RAG) approach, where the system retrieves the most relevant chunks from the vector database and uses them to construct a detailed prompt for the large language model (LLM). The LLM then generates accurate and contextually relevant responses.

## Technologies Used

- **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.6+.
- **LangChain:** A framework for developing applications powered by language models, allowing integration with vector databases and document loaders.
- **Vector Database:** Used to index and retrieve the most relevant information from the uploaded PDFs.

## How It Works

1. **Upload PDFs:** Users upload their PDF documents through the `/upload_pdf` endpoint. The service processes the documents and stores the text chunks in a vector database.
   
2. **Ask Questions:** Users can ask questions via the `/ask_question` endpoint. The service retrieves relevant chunks based on the user's previous uploads and uses them to provide accurate answers.

3. **Personalization:** The agent uses the user ID to filter and retrieve information specific to the individual user, ensuring that responses are personalized and based on their uploaded documents.

## Setting Up the Project

To set up and run the project locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/nadheesh/personalized-chat-agent.git
   cd chat-agent-with-pdf/backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   - **OPENAI_API_KEY**: Your OpenAI API key.
   - **PINECONE_API_KEY**: Your Pinecone API key.
   - **PINECONE_INDEX_NAME**: The name of the Pinecone index that holds the data.

   You can set these environment variables in your terminal session with:

   ```bash
   export OPENAI_API_KEY='your-openai-api-key'
   export PINECONE_API_KEY='your-pinecone-api-key'
   export PINECONE_INDEX_NAME='your-pinecone-index-name'
   ```

   Alternatively, you can create a `.env` file in the root of your project and add the following lines:

   ```env
   OPENAI_API_KEY=your-openai-api-key
   PINECONE_API_KEY=your-pinecone-api-key
   PINECONE_INDEX_NAME=your-pinecone-index-name
   ```

4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload 
   ```

5. The service will be available at `http://127.0.0.1:8000`.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, feel free to open an issue or submit a pull request.
