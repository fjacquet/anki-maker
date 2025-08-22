# Document to Anki Web Frontend

This directory contains the web frontend implementation for the Document to Anki Converter application. The frontend provides a modern, accessible, and responsive web interface for converting documents into Anki flashcards using AI.

## Features

### Core Functionality
- **Drag & Drop File Upload**: Intuitive file upload with visual feedback
- **Multiple File Support**: Upload single files, folders, or ZIP archives
- **Real-time Progress Tracking**: Live progress updates during processing
- **Interactive Flashcard Management**: Preview, edit, add, and delete flashcards
- **CSV Export**: Download Anki-compatible CSV files
- **Session Management**: Maintain state across the conversion workflow

### User Experience
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Professional UI**: Clean, modern interface with smooth animations
- **Real-time Feedback**: Immediate visual feedback for all user actions
- **Progress Indicators**: Clear progress bars and status messages
- **Error Handling**: User-friendly error messages with actionable guidance

### Accessibility (WCAG 2.1 AA Compliant)
- **Screen Reader Support**: Full compatibility with assistive technologies
- **Keyboard Navigation**: Complete keyboard accessibility
- **Focus Management**: Proper focus indicators and management
- **ARIA Labels**: Comprehensive ARIA attributes for screen readers
- **High Contrast Support**: Automatic adaptation to user preferences
- **Reduced Motion**: Respects user's motion preferences
- **Skip Links**: Navigation shortcuts for screen reader users

### Progressive Web App (PWA)
- **Offline Support**: Service worker for offline functionality
- **App-like Experience**: Can be installed as a native app
- **Fast Loading**: Cached resources for improved performance
- **Push Notifications**: Ready for notification support (future enhancement)

## File Structure

```
web/
├── app.py                 # FastAPI application with all API endpoints
├── templates/
│   └── index.html        # Main HTML template with embedded styles
├── static/
│   ├── style.css         # Enhanced CSS with animations and accessibility
│   ├── app.js           # Main JavaScript application logic
│   ├── sw.js            # Service worker for offline support
│   ├── manifest.json    # PWA manifest file
│   └── favicon.ico      # Application icon
└── README.md            # This file
```

## Technical Implementation

### Frontend Architecture
- **Vanilla JavaScript**: No framework dependencies for maximum compatibility
- **Class-based Structure**: Organized code with DocumentToAnkiApp class
- **Event-driven**: Responsive to user interactions and API responses
- **Modular Design**: Separated concerns for maintainability

### API Integration
- **RESTful API**: Clean integration with FastAPI backend
- **Async/Await**: Modern JavaScript for API calls
- **Error Handling**: Comprehensive error handling and user feedback
- **Progress Polling**: Real-time status updates during processing
- **File Upload**: Multipart form data with progress tracking

### Accessibility Features
- **Semantic HTML**: Proper HTML5 semantic elements
- **ARIA Attributes**: Comprehensive accessibility attributes
- **Focus Management**: Proper focus handling for modals and interactions
- **Screen Reader Announcements**: Live regions for dynamic content
- **Keyboard Shortcuts**: Convenient keyboard shortcuts (Ctrl+U, Ctrl+E, Ctrl+N)
- **Skip Links**: Navigation shortcuts for assistive technologies

### Responsive Design
- **Mobile-First**: Designed for mobile devices first
- **CSS Grid/Flexbox**: Modern layout techniques
- **Breakpoints**: Optimized for different screen sizes
- **Touch-Friendly**: Large touch targets for mobile devices
- **Print Styles**: Optimized for printing flashcards

### Performance Optimizations
- **Service Worker**: Caching for offline support and faster loading
- **Lazy Loading**: Efficient resource loading
- **Minimal Dependencies**: No external JavaScript libraries
- **Optimized Images**: Placeholder for optimized icon files
- **Compressed Assets**: Ready for asset compression

## Browser Support

### Minimum Requirements
- **Modern Browsers**: Chrome 60+, Firefox 55+, Safari 12+, Edge 79+
- **JavaScript**: ES6+ support required
- **CSS**: CSS Grid and Flexbox support
- **APIs**: Fetch API, FormData, FileReader, localStorage

### Progressive Enhancement
- **Core Functionality**: Works without JavaScript (form submission)
- **Enhanced Experience**: Full features with JavaScript enabled
- **Offline Support**: Service worker for supported browsers
- **PWA Features**: Installation and app-like experience where supported

## Accessibility Compliance

### WCAG 2.1 AA Standards
- **Perceivable**: High contrast, scalable text, alternative text
- **Operable**: Keyboard navigation, no seizure-inducing content
- **Understandable**: Clear language, consistent navigation
- **Robust**: Compatible with assistive technologies

### Testing
- **Screen Readers**: Tested with NVDA, JAWS, VoiceOver
- **Keyboard Navigation**: Full keyboard accessibility
- **Color Contrast**: Meets WCAG AA contrast requirements
- **Focus Indicators**: Clear focus indicators throughout

## Development

### Local Development
```bash
# Start the FastAPI server
python -m uvicorn document_to_anki.web.app:app --reload --host 0.0.0.0 --port 8000

# Access the application
open http://localhost:8000
```

### Testing
- **Manual Testing**: Cross-browser and device testing
- **Accessibility Testing**: Screen reader and keyboard testing
- **Performance Testing**: Lighthouse audits
- **Responsive Testing**: Multiple device sizes

### Code Quality
- **ESLint**: JavaScript linting (configuration ready)
- **Prettier**: Code formatting (configuration ready)
- **Accessibility Linting**: axe-core integration ready
- **Performance Monitoring**: Web Vitals tracking ready

## Deployment

### Production Considerations
- **Asset Optimization**: Minify CSS and JavaScript
- **Image Optimization**: Compress and optimize images
- **CDN**: Serve static assets from CDN
- **Caching**: Proper HTTP caching headers
- **Security**: CSP headers and security best practices

### Environment Variables
- **API_BASE_URL**: Base URL for API endpoints (if different from current domain)
- **ENVIRONMENT**: Production/development environment flag

## Future Enhancements

### Planned Features
- **Batch Processing**: Multiple document processing queues
- **User Accounts**: Save and manage flashcard collections
- **Collaboration**: Share flashcard sets with others
- **Advanced Editing**: Rich text editor for flashcards
- **Templates**: Predefined flashcard templates
- **Analytics**: Usage analytics and insights

### Technical Improvements
- **WebAssembly**: Client-side document processing
- **WebRTC**: Real-time collaboration features
- **IndexedDB**: Client-side storage for offline work
- **Push Notifications**: Processing completion notifications
- **Background Sync**: Retry failed uploads automatically

## Contributing

### Code Style
- **Consistent Formatting**: Use Prettier for formatting
- **Semantic Naming**: Clear, descriptive variable and function names
- **Comments**: Document complex logic and accessibility features
- **Accessibility First**: Consider accessibility in all changes

### Testing Requirements
- **Cross-browser Testing**: Test in multiple browsers
- **Accessibility Testing**: Verify with screen readers
- **Mobile Testing**: Test on actual mobile devices
- **Performance Testing**: Ensure good performance scores

## License

This web frontend is part of the Document to Anki Converter project and follows the same license terms as the main project.