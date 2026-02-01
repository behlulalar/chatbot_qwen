import React from 'react';
import ChatInterface from './components/ChatInterface';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <div className="App">
        <ChatInterface />
      </div>
    </ErrorBoundary>
  );
}

export default App;
