import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import './App.css';

// Main App Component
function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [todoistTasks, setTodoistTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
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
      <div className="sidebar">
        <div className="sidebar-header">
        </div>

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
                  <div className="event-title">{event.summary}</div>
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
          </div>
          <div className="todoist-tasks">
            {todoistTasks.filter(task => !task.completed).length > 0 ? (
              todoistTasks
                .filter(task => !task.completed)
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

        {/* Insurance Chatbot Widget */}
        <div className="widget fade-in">
          <div className="widget-header">
            <i className="fas fa-shield-alt"></i>
            <h3>Insurance Assistant</h3>
          </div>
          <div className="insurance-chat">
            <div className="insurance-message">
              Need help with insurance claims?
            </div>
          </div>
          <button className="insurance-button" onClick={startInsuranceChat}>
            <i className="fas fa-comments"></i> Start Insurance Chat
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="main-chat">
        <div className="chat-header">
          <div className="chat-header-avatar">
            <img src="/logo.png" alt="AHMA Logo" className="ahma-logo-small" />
          </div>
          <div className="chat-header-info">
            <h2>AHMA</h2>
            <p>Advanced Healthcare Management Assistant</p>
          </div>
        </div>

        <div className="chat-container">
          {messages.map(message => (
            <div key={message.id} className={`message ${message.sender} slide-in`}>
              <div className="message-content" dangerouslySetInnerHTML={{ __html: message.content }}></div>
            </div>
          ))}
          
          {isTyping && (
            <div className="message assistant">
              <div className="message-content">
                <div className="loading">
                  <div className="loading-spinner"></div>
                  AHMA is typing...
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

