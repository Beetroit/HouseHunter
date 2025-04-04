import React, { useCallback, useEffect, useRef, useState } from 'react'; // Import useRef
import { useAuth } from '../../contexts/AuthContext.jsx'; // Import useAuth
import useChatWebSocket from '../../hooks/useChatWebSocket.js'; // Import the hook
import apiService from '../../services/apiService.jsx'; // Import apiService
import './ChatStyles.css';

// MessageList component modified to accept a ref
const MessageList = React.forwardRef(({ messages }, ref) => ( // Use React.forwardRef
    <ul className="message-list" ref={ref}> {/* Attach the ref here */}
        {messages.map((msg, index) => (
            // Use message ID if available and unique, otherwise fallback to index
            <li key={msg.id || index} className={msg.isOwn ? 'own-message' : 'other-message'}>
                <strong>{msg.senderName}:</strong> {msg.text}
                {/* Optionally display timestamp */}
                {/* <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span> */}
            </li>
        ))}
    </ul>
));

// Placeholder component until MessageInput is created
const MessageInput = ({ onSendMessage, disabled }) => { // Add disabled prop
    const [message, setMessage] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim() && !disabled) { // Check disabled state
            onSendMessage(message);
            setMessage('');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="message-input-form">
            <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={disabled ? "Connecting..." : "Type your message..."}
                aria-label="Chat message input"
                disabled={disabled} // Disable input based on prop
            />
            <button type="submit" disabled={disabled}>Send</button> {/* Disable button */}
        </form>
    );
};

// Main ChatWindow component
function ChatWindow({ chatId }) { // Expect only chatId as prop
    const { currentUser } = useAuth(); // Get current user from AuthContext
    const [messages, setMessages] = useState([]);
    const [error, setError] = useState(null); // Local UI/error state
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const messagesEndRef = useRef(null); // Ref for the message list container

    // Integrate with useChatWebSocket hook
    const { sendMessage, lastMessage, connectionStatus, error: wsError } = useChatWebSocket(chatId);

    // Function to scroll the message list to the bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollTo({ top: messagesEndRef.current.scrollHeight, behavior: 'smooth' });
    };

    // Update local messages state when a new message arrives via WebSocket
    useEffect(() => {
        if (lastMessage) {
            // Determine if the message is from the current user
            const isOwn = lastMessage.sender && currentUser && lastMessage.sender.id === currentUser.id;
            const senderName = isOwn ? 'Me' : (lastMessage.sender?.email || 'Unknown User'); // Use email as name for now

            // Avoid adding duplicates if message already exists (simple check by id)
            setMessages(prevMessages => {
                if (prevMessages.some(msg => msg.id === lastMessage.id)) {
                    return prevMessages;
                }
                return [
                    ...prevMessages,
                    {
                        id: lastMessage.id,
                        text: lastMessage.content,
                        senderId: lastMessage.sender?.id,
                        senderName: senderName,
                        timestamp: lastMessage.created_at,
                        isOwn: isOwn,
                    }
                ];
            });
            // Scroll to bottom after adding new message
            // Use setTimeout to allow DOM update before scrolling
            setTimeout(scrollToBottom, 0);
        }
    }, [lastMessage, currentUser]); // Depend on lastMessage and currentUser

    // Handle WebSocket errors reported by the hook
    useEffect(() => {
        if (wsError) {
            setError(`WebSocket Error: ${wsError}`);
            // Optionally clear the error after some time
        }
    }, [wsError]);

    // Fetch initial message history
    useEffect(() => {
        const fetchHistory = async () => {
            if (!chatId) return;
            console.log(`Fetching history for chat ${chatId}`);
            setIsLoadingHistory(true);
            setError(null); // Clear previous errors
            try {
                // Future enhancement: Implement pagination for history loading if needed (e.g., load more button)
                const historyData = await apiService.getChatMessages(chatId, 1, 50); // Fetch first 50 messages
                const formattedHistory = historyData.items.map(msg => {
                    const isOwn = msg.sender && currentUser && msg.sender.id === currentUser.id;
                    const senderName = isOwn ? 'Me' : (msg.sender?.email || 'Unknown User');
                    return {
                        id: msg.id,
                        text: msg.content,
                        senderId: msg.sender?.id,
                        senderName: senderName,
                        timestamp: msg.created_at,
                        isOwn: isOwn,
                    };
                }).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)); // Ensure history is sorted chronologically
                setMessages(formattedHistory);
                // Scroll to bottom after loading history
                // Use setTimeout to allow DOM update before scrolling
                setTimeout(scrollToBottom, 0);
            } catch (err) {
                console.error(`Failed to load chat history for ${chatId}:`, err);
                setError(`Failed to load message history: ${err.message}`);
            } finally {
                setIsLoadingHistory(false);
            }
        };

        fetchHistory();
        // Clear messages when chat ID changes before loading new history
        return () => setMessages([]);
    }, [chatId, currentUser]); // Depend on chatId and currentUser (for isOwn check)


    // Use the sendMessage function from the hook
    const handleSendMessage = useCallback((messageText) => {
        if (connectionStatus === 'Open') {
            sendMessage({ content: messageText });
        } else {
            setError("Cannot send message: Connection is not open.");
            console.warn("Attempted to send message while WebSocket was not open.");
        }
    }, [sendMessage, connectionStatus]);

    // Determine connection status display
    const isConnected = connectionStatus === 'Open';
    const statusText = error || connectionStatus; // Show error message if present
    const statusClass = isConnected ? 'connected' : (connectionStatus === 'Connecting' ? 'connecting' : 'disconnected');

    return (
        <div className="chat-window">
            <h3>Chat Room {chatId ? `(${chatId.substring(0, 8)}...)` : ''}</h3>
            <div className={`connection-status ${statusClass}`}>
                Status: {statusText}
            </div>
            {/* Display loading indicator */}
            {isLoadingHistory && <p style={{ textAlign: 'center', padding: '1rem' }}>Loading history...</p>}
            {/* Error display is now part of statusText, but keep separate UI error if needed */}
            {/* {error && !wsError && <div className="error-message">UI Error: {error}</div>} */}
            <MessageList messages={messages} ref={messagesEndRef} /> {/* Pass the ref */}
            <MessageInput onSendMessage={handleSendMessage} disabled={!isConnected || isLoadingHistory} /> {/* Disable input if not connected or loading */}
        </div>
    );
}

export default ChatWindow;