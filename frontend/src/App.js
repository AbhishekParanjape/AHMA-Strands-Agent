import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import ReactMarkdown from 'react-markdown';
import './App.css';

// Main App Component
function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [todoistTasks, setTodoistTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [pdfFiles, setPdfFiles] = useState({ uploaded: [], processed: [] });
  const [isProcessingPdf, setIsProcessingPdf] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load initial data
    loadCalendarEvents();
    loadTodoistTasks();
    loadPdfFiles();
    setIsLoading(false);

    // Add welcome message
    setMessages([
      {
        id: 1,
        sender: 'assistant',
        content: `Hello Hazel! I'm AHMA, your Advanced Healthcare Management Assistant. How can I assist you today?`,
        timestamp: new Date()
      }
    ]);

    // Set up periodic refresh for tasks (every 30 seconds)
    const taskRefreshInterval = setInterval(() => {
      loadTodoistTasks();
    }, 30000);

    // Cleanup interval on component unmount
    return () => clearInterval(taskRefreshInterval);
  }, []);

  // Load Google Calendar Events
  const loadCalendarEvents = async () => {
    try {
      const response = await fetch('/api/google-calendar/events?max_results=5');
      const data = await response.json();
      setCalendarEvents(data.events || []);
    } catch (error) {
      console.error('Error loading calendar events:', error);
      setCalendarEvents([]);
    }
  };

  // Load Todoist Tasks
  const loadTodoistTasks = async () => {
    try {
      const response = await fetch('/api/todoist/tasks?limit=10');
      const data = await response.json();
      setTodoistTasks(data.tasks || []);
    } catch (error) {
      console.error('Error loading Todoist tasks:', error);
      setTodoistTasks([]);
    }
  };

  // Load PDF Files
  const loadPdfFiles = async () => {
    try {
      const response = await fetch('/api/pdf/list');
      const data = await response.json();
      if (data.success) {
        setPdfFiles({
          uploaded: data.uploaded_files || [],
          processed: data.processed_files || []
        });
      }
    } catch (error) {
      console.error('Error loading PDF files:', error);
      setPdfFiles({ uploaded: [], processed: [] });
    }
  };

  // Upload PDF File
  const uploadPdf = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/pdf/upload', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (data.success) {
        loadPdfFiles(); // Reload PDF list
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'assistant',
          content: `✅ PDF uploaded successfully: ${data.filename}`,
          timestamp: new Date()
        }]);
        return true;
      } else {
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'assistant',
          content: `❌ Upload failed: ${data.error}`,
          timestamp: new Date()
        }]);
        return false;
      }
    } catch (error) {
      console.error('Error uploading PDF:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        content: '❌ Error uploading PDF. Please try again.',
        timestamp: new Date()
      }]);
      return false;
    }
  };

  // Process PDF File
  const processPdf = async (filename, formType = 'auto') => {
    try {
      setIsProcessingPdf(true);
      const response = await fetch('/api/pdf/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename, form_type: formType })
      });

      const data = await response.json();
      if (data.success) {
        loadPdfFiles(); // Reload PDF list
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'assistant',
          content: `✅ PDF processed successfully! Filled form saved as: ${data.processed_filename}`,
          timestamp: new Date()
        }]);
        return true;
      } else {
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'assistant',
          content: `❌ Processing failed: ${data.error}`,
          timestamp: new Date()
        }]);
        return false;
      }
    } catch (error) {
      console.error('Error processing PDF:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        content: '❌ Error processing PDF. Please try again.',
        timestamp: new Date()
      }]);
      return false;
    } finally {
      setIsProcessingPdf(false);
    }
  };

  // Download PDF File
  const downloadPdf = async (filename, type = 'processed') => {
    try {
      const response = await fetch(`/api/pdf/download/${filename}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'assistant',
          content: '❌ Error downloading PDF. File may not exist.',
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      console.error('Error downloading PDF:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        content: '❌ Error downloading PDF. Please try again.',
        timestamp: new Date()
      }]);
    }
  };

  // Handle File Upload
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      uploadPdf(file);
    } else {
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        content: '❌ Please select a valid PDF file.',
        timestamp: new Date()
      }]);
    }
    event.target.value = ''; // Reset input
  };

  // Send Message
  const sendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/ahma/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: inputMessage })
      });

      const data = await response.json();
      
      const assistantMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        content: data.response || 'Sorry, I encountered an error.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  // Complete Todoist Task
  const completeTask = async (taskId) => {
    try {
      const response = await fetch(`/api/todoist/tasks/${taskId}/complete`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        loadTodoistTasks(); // Reload tasks
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'assistant',
          content: 'Task completed successfully!',
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      console.error('Error completing task:', error);
    }
  };

  // Start Insurance Chat
  const startInsuranceChat = () => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      sender: 'assistant',
      content: 'Insurance Assistant: Hello! I can help you with insurance claims, policy questions, and coverage information. What would you like to know?',
      timestamp: new Date()
    }]);
  };

  // Handle Enter Key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading AHMA...</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <button 
          className="sidebar-toggle"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          <i className={`fas fa-chevron-${sidebarCollapsed ? 'right' : 'left'}`}></i>
        </button>
        
        <div className="sidebar-header">
          <h1>AHMA</h1>
          <p>Advanced Healthcare Management Assistant</p>
        </div>

        <div className="widgets-container">
          {/* Google Calendar Widget */}
          <div className="widget fade-in">
          <div className="widget-header">
            <i className="fas fa-calendar-alt"></i>
            <h3>Google Calendar</h3>
          </div>
          <div className="calendar-events">
            {calendarEvents.length > 0 ? (
              calendarEvents.map(event => (
                <div key={event.id} className="event-item slide-in">
                  <div className="event-time">
                    <i className="fas fa-clock"></i>
                    {new Date(event.start).toLocaleString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true
                    })}
                  </div>
                  <div className="event-title">{event.summary}</div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <i className="fas fa-calendar-times"></i>
                <p>No upcoming events</p>
              </div>
            )}
          </div>
        </div>

        {/* Todoist Widget */}
        <div className="widget fade-in">
          <div className="widget-header">
            <i className="fas fa-tasks"></i>
            <h3>Todoist Tasks</h3>
            <button 
              className="refresh-button"
              onClick={loadTodoistTasks}
              title="Refresh tasks"
            >
              <i className="fas fa-sync-alt"></i>
            </button>
          </div>
          <div className="todoist-tasks">
            {todoistTasks.filter(task => !task.completed).length > 0 ? (
              todoistTasks
                .filter(task => !task.completed)
                .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) // Sort by creation date, newest first
                .map(task => (
                  <div key={task.id} className="task-item slide-in">
                    <i 
                      className="fas fa-circle task-checkbox" 
                      onClick={() => completeTask(task.id)}
                    ></i>
                    <div className="task-content">
                      <div>{task.content}</div>
                      <div className="task-priority">
                        Priority: {['Low', 'Medium', 'High', 'Urgent'][task.priority - 1] || 'Low'}
                      </div>
                    </div>
                  </div>
                ))
            ) : (
              <div className="empty-state">
                <i className="fas fa-check-circle"></i>
                <p>All tasks completed!</p>
              </div>
            )}
          </div>
        </div>

        {/* Insurance & PDF Processing Widget */}
        <div className="widget fade-in">
          <div className="widget-header">
            <i className="fas fa-shield-alt"></i>
            <h3>Insurance & PDF Forms</h3>
          </div>
          
          {/* PDF Upload Section */}
          <div className="pdf-upload-section">
            <div className="upload-area">
              <input
                type="file"
                id="pdf-upload"
                accept=".pdf"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              <label htmlFor="pdf-upload" className="upload-button">
                <i className="fas fa-upload"></i> Upload PDF Form
              </label>
            </div>
          </div>

          {/* Uploaded PDFs */}
          {pdfFiles.uploaded.length > 0 && (
            <div className="pdf-list">
              <h4><i className="fas fa-file-pdf"></i> Uploaded Forms</h4>
              {pdfFiles.uploaded.map((file, index) => (
                <div key={index} className="pdf-file-item">
                  <div className="pdf-file-info">
                    <div className="pdf-name">{file.filename}</div>
                    <div className="pdf-size">({(file.size / 1024).toFixed(1)} KB)</div>
                  </div>
                  <div className="pdf-actions">
                    <button 
                      className="process-button"
                      onClick={() => processPdf(file.filename, 'auto')}
                      disabled={isProcessingPdf}
                    >
                      {isProcessingPdf ? '⏳' : '⚡'} Process
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Processed PDFs */}
          {pdfFiles.processed.length > 0 && (
            <div className="pdf-list">
              <h4><i className="fas fa-check-circle"></i> Filled Forms</h4>
              {pdfFiles.processed.map((file, index) => (
                <div key={index} className="pdf-file-item">
                  <div className="pdf-file-info">
                    <div className="pdf-name">{file.filename}</div>
                    <div className="pdf-size">({(file.size / 1024).toFixed(1)} KB)</div>
                  </div>
                  <div className="pdf-actions">
                    <button 
                      className="download-button"
                      onClick={() => downloadPdf(file.filename)}
                    >
                      <i className="fas fa-download"></i> Download
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-container">
        <div className="chat-header">
          <h2>AHMA</h2>
        </div>

        <div className="chat-messages">
          {messages.map(message => (
            <div key={message.id} className={`message ${message.sender} slide-in`}>
              {message.sender === 'user' ? (
                <>
                  <div className="message-content">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                  <div className="message-timestamp">
                    {new Date(message.timestamp).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true
                    })}
                  </div>
                  <div className="message-icon"></div>
                </>
              ) : (
                <>
                  <div className="message-content">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                  <div className="message-timestamp">
                    {new Date(message.timestamp).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true
                    })}
                  </div>
                  <div className="message-icon"></div>
                </>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div className="message assistant">
              <div className="typing-indicator">
                <div className="message-icon"></div>
                <div className="typing-dots">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <input 
            type="text" 
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            className="chat-input" 
            placeholder="Type your message here..." 
          />
          <button 
            className={`send-button ${!inputMessage.trim() || isTyping ? 'disabled' : ''}`}
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isTyping}
          >
            <i className="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>
  );
}

// Render the app
ReactDOM.render(<App />, document.getElementById('root'));

export default App;

