// frontend/src/pages/ChatsListPage.jsx
import React, { useContext, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext.jsx'; // To identify the current user
import apiService from '../services/apiService.jsx';
import './ChatsListStyles.css'; // Create this CSS file next

function ChatsListPage() {
    const { currentUser } = useContext(AuthContext);
    const [chats, setChats] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const perPage = 20; // Or make this configurable

    useEffect(() => {
        const fetchChats = async () => {
            if (!currentUser) return; // Should be protected by route, but good practice

            setLoading(true);
            setError('');
            try {
                const response = await apiService.getMyChatSessions({ page: page, per_page: perPage });
                setChats(response.items || []);
                setPage(response.page);
                setTotalPages(response.total_pages);
            } catch (err) {
                console.error("Failed to fetch chat sessions:", err);
                setError(err.message || 'Failed to load chat sessions.');
            } finally {
                setLoading(false);
            }
        };

        fetchChats();
    }, [page, currentUser]); // Re-fetch if page or user changes

    const getOtherParticipant = (chat) => {
        if (!currentUser) return null;
        if (chat.initiator?.id === currentUser.id) {
            return chat.property_user; // 'property_user' is the other participant
        }
        if (chat.property_user?.id === currentUser.id) {
            return chat.initiator;
        }
        return null; // Should not happen if currentUser is participant
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString(); // Basic formatting
    };

    return (
        <div className="chats-list-container">
            <h2>My Chats</h2>
            {loading && <p>Loading chats...</p>}
            {error && <p className="error-message">{error}</p>}
            {!loading && !error && chats.length === 0 && <p>You have no active chats.</p>}
            {!loading && !error && chats.length > 0 && (
                <ul className="chats-list">
                    {chats.map(chat => {
                        const otherParticipant = getOtherParticipant(chat);
                        return (
                            <li key={chat.id} className="chat-list-item">
                                <Link to={`/chat/${chat.id}`}>
                                    <div className="chat-item-info">
                                        <span className="chat-participant-name">
                                            {otherParticipant ? `${otherParticipant.first_name || ''} ${otherParticipant.last_name || ''}`.trim() || otherParticipant.email : 'Unknown User'}
                                        </span>
                                        {/* Optionally show property title if available */}
                                        {/* {chat.property && <span className="chat-property-title">({chat.property.title})</span>} */}
                                        <span className="chat-last-updated">
                                            Last updated: {formatTimestamp(chat.updated_at)}
                                        </span>
                                    </div>
                                    {/* Add unread indicator later */}
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            )}

            {/* Pagination Controls */}
            {!loading && totalPages > 1 && (
                <div className="pagination-controls" style={{ marginTop: '2rem', textAlign: 'center' }}>
                    <button
                        onClick={() => setPage(prev => Math.max(prev - 1, 1))}
                        disabled={page <= 1 || loading}
                        style={{ marginRight: '1rem' }}
                    >
                        Previous
                    </button>
                    <span>Page {page} of {totalPages}</span>
                    <button
                        onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={page >= totalPages || loading}
                        style={{ marginLeft: '1rem' }}
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    );
}

export default ChatsListPage;