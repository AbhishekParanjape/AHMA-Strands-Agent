# AHMA Frontend

A modern, responsive frontend for AHMA (AI Health Management Assistant) built with React and featuring real-time integration with Google Calendar and Todoist APIs.

## Features

### 🎨 **Modern UI/UX**
- Beautiful gradient backgrounds and glassmorphism effects
- Smooth animations and transitions
- Responsive design for all devices
- Dark mode support
- Accessibility features

### 🤖 **AHMA Chatbot**
- Real-time chat interface with typing indicators
- Message history and conversation management
- Dark red (#800000) branding as requested
- Intelligent responses with context awareness

### 📅 **Google Calendar Widget**
- Real-time calendar events display
- Event details with formatted timestamps
- Hover effects and smooth animations
- Auto-refresh every 5 minutes

### 📝 **Todoist Widget**
- Live task management interface
- Click-to-complete functionality
- Priority level indicators
- Task filtering (incomplete tasks only)

### 🏥 **Insurance Assistant Widget**
- Quick access to insurance assistance
- Specialized insurance chat functionality
- Seamless integration with main chat

## Tech Stack

- **React 18** - Modern React with hooks
- **CSS3** - Custom styling with animations
- **Font Awesome** - Icon library
- **Axios** - HTTP client for API calls
- **React Router** - Navigation (if needed)
- **Framer Motion** - Advanced animations

## Project Structure

```
frontend/
├── public/
│   └── index.html          # Main HTML file
├── src/
│   ├── App.js              # Main React component
│   ├── App.css             # Main styles
│   ├── index.js            # React entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
└── README.md              # This file
```

## Installation & Setup

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn
- Backend server running on port 5000

### Installation Steps

1. **Navigate to the frontend directory:**
   ```bash
   cd clueless/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

### Development Features

- **Hot Reloading** - Changes reflect immediately
- **Proxy Configuration** - API calls proxy to backend
- **Error Boundaries** - Graceful error handling
- **Console Logging** - Detailed debugging information

## API Integration

### Backend Endpoints Used

- `POST /api/ahma/chat` - Send messages to AHMA
- `GET /api/google-calendar/events` - Fetch calendar events
- `GET /api/todoist/tasks` - Fetch Todoist tasks
- `POST /api/todoist/tasks/{id}/complete` - Complete tasks

### Error Handling

- Network error handling with user-friendly messages
- Loading states for all API calls
- Graceful fallbacks for missing data
- Retry mechanisms for failed requests

## Styling & Design

### Color Scheme
- **Primary**: #800000 (Dark Red) - AHMA branding
- **Secondary**: #2c3e50 (Dark Blue) - Sidebar
- **Accent**: #27ae60 (Green) - Success states
- **Background**: Gradient from #667eea to #764ba2

### Design Principles
- **Glassmorphism** - Translucent elements with blur effects
- **Micro-interactions** - Hover effects and smooth transitions
- **Responsive Design** - Mobile-first approach
- **Accessibility** - Keyboard navigation and screen reader support

## Component Architecture

### Main Components

1. **App** - Main application container
2. **Sidebar** - Widget container
3. **ChatArea** - Main chat interface
4. **Widget** - Reusable widget component
5. **Message** - Individual chat message

### State Management

- **React Hooks** - useState, useEffect, useRef
- **Local State** - Component-level state management
- **API State** - Loading, error, and data states

## Performance Optimizations

- **Lazy Loading** - Components load on demand
- **Memoization** - Prevent unnecessary re-renders
- **Debounced Input** - Reduce API calls
- **Optimized Images** - WebP format support

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Mobile Responsiveness

### Breakpoints
- **Desktop**: 1200px+
- **Tablet**: 768px - 1199px
- **Mobile**: < 768px

### Mobile Features
- Touch-friendly interface
- Swipe gestures
- Optimized layouts
- Reduced animations for performance

## Accessibility

- **ARIA Labels** - Screen reader support
- **Keyboard Navigation** - Full keyboard accessibility
- **Focus Management** - Proper focus indicators
- **Color Contrast** - WCAG AA compliance

## Testing

### Manual Testing Checklist
- [ ] Chat functionality works correctly
- [ ] Calendar events load and display
- [ ] Todoist tasks load and can be completed
- [ ] Insurance chat starts properly
- [ ] Responsive design works on all screen sizes
- [ ] Keyboard navigation functions
- [ ] Error states display properly

## Deployment

### Build for Production
```bash
npm run build
```

### Deployment Options
- **Netlify** - Drag and drop deployment
- **Vercel** - Git-based deployment
- **AWS S3** - Static hosting
- **GitHub Pages** - Free hosting

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Ensure backend is running on port 5000
   - Check CORS configuration
   - Verify API endpoints

2. **Styling Issues**
   - Clear browser cache
   - Check CSS specificity
   - Verify Font Awesome loading

3. **Performance Issues**
   - Check network tab for slow requests
   - Optimize images and assets
   - Reduce bundle size

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the AHMA (AI Health Management Assistant) system.

## Support

For support and questions:
- Check the troubleshooting section
- Review the backend documentation
- Open an issue on GitHub

