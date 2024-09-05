// ChatInterface.js
import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { marked } from 'marked';

function ChatInterface({ userInfo, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [userId] = useState(() => sessionStorage.getItem('userId') || uuidv4());
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const chatMessagesRef = useRef(null);

  useEffect(() => {
    sessionStorage.setItem('userId', userId);
  }, [userId]);

  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [messages]);

  const callApi = async (endpoint, options = {}) => {
    const response = await fetch(`/choreo-apis/${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Content-Type': 'application/json',
      },
    });
    return response.json();
  };

  const sendMessage = async () => {
    if (inputMessage.trim() && !isTyping && !isUploading) {
      addMessageToChat('user', inputMessage);
      setInputMessage('');
      setIsTyping(true);

      try {
        const data = await callApi('ask_question', {
          method: 'POST',
          body: JSON.stringify({
            user_id: userId,
            message: inputMessage,
            chat_history: chatHistory
          }),
        });

        if (data && data.response) {
          addMessageToChat('ai', data.response, true);
          updateChatHistory('human', inputMessage);
          updateChatHistory('ai', data.response);
        } else {
          throw new Error('Invalid response from server');
        }
      } catch (error) {
        console.error('Error:', error);
        addMessageToChat('ai', 'Sorry, there was an error processing your request. Please try again later.');
      } finally {
        setIsTyping(false);
      }
    }
  };

  const addMessageToChat = (role, content, isMarkdown = false) => {
    let processedContent = content;
    if (isMarkdown && content) {
      try {
        processedContent = marked(content);
      } catch (error) {
        console.error('Error parsing markdown:', error);
        processedContent = content;
      }
    }
    setMessages(prevMessages => [...prevMessages, { role, content: processedContent, isMarkdown }]);
  };

  const addSystemMessage = (message) => {
    setMessages(prevMessages => [...prevMessages, { role: 'system', content: message }]);
  };

  const updateChatHistory = (role, content) => {
    setChatHistory(prevHistory => {
      const newHistory = [...prevHistory, { role, content }];
      return newHistory.slice(-5);
    });
  };

  const uploadPDF = async (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadStatus('Uploading...');
      setIsUploading(true);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);

      try {
        const data = await callApi('add_data', {
          method: 'POST',
          body: formData,
        });
        setUploadStatus('Upload successful!');
        addSystemMessage(`Uploaded ${file.name}`);
      } catch (error) {
        console.error('Error:', error);
        setUploadStatus('Upload failed. Please try again.');
      } finally {
        setIsUploading(false);
      }
    }
  };

  return (
    <div className="container">
      <div className="user-info">
        Welcome, {userInfo.name}! <button onClick={onLogout}>Logout</button>
      </div>
      <div className="left-panel">
        <h2>Document Upload</h2>
        <div className="upload-area">
          <input type="file" id="pdf-upload" accept=".pdf" onChange={uploadPDF} disabled={isTyping || isUploading} />
          <label htmlFor="pdf-upload" id="upload-button">
            <i className="fas fa-cloud-upload-alt"></i> Choose PDF
          </label>
          {isUploading && <div className="loader" id="upload-loader"></div>}
          <p id="upload-status">{uploadStatus}</p>
        </div>
      </div>
      <div className="chat-area">
        <div className="chat-header">
          AI Assistant
        </div>
        <div className="chat-messages" ref={chatMessagesRef}>
          {messages.map((message, index) => (
            message.role === 'system' ? (
              <div key={index} className="system-message">{message.content}</div>
            ) : (
              <div key={index} className={`message ${message.role}`}>
                <div className="avatar">{message.role === 'user' ? 'U' : 'AI'}</div>
                <div
                  className="message-content"
                  dangerouslySetInnerHTML={{ __html: message.isMarkdown ? message.content : message.content }}
                ></div>
              </div>
            )
          ))}
        </div>
        {isTyping && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <div className="input-area">
          <input
            type="text"
            id="chat-input"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            disabled={isTyping || isUploading}
          />
          <button id="send-button" onClick={sendMessage} disabled={isTyping || isUploading}>
            <i className="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;