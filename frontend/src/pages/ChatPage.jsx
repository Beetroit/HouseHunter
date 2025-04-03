import React from 'react';
import { useParams } from 'react-router-dom';
import ChatWindow from '../components/chat/ChatWindow.jsx';
// import { useAuth } from '../contexts/AuthContext.jsx'; // Might need auth context later

function ChatPage() {
    const { chatId } = useParams(); // Get chat ID from URL parameter
    // const { currentUser } = useAuth(); // Get current user if needed for other info

    if (!chatId) {
        // Handle case where chatId is missing, though route setup should prevent this
        return <p className="error-message">Error: Chat ID is missing.</p>;
    }

    return (
        <div className="chat-page-container" style={{ maxWidth: '800px', margin: '1rem auto' }}>
            <h2>Chat Session</h2>
            {/* Render the ChatWindow component, passing the chatId */}
            {/* ChatWindow now gets currentUser from context internally */}
            <ChatWindow chatId={chatId} />
            {/* Add any other relevant info or controls for the chat page here */}
        </div>
    );
}

export default ChatPage;