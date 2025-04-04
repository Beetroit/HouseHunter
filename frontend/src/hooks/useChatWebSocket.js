import { useCallback, useEffect, useRef, useState } from 'react';

const WEBSOCKET_READY_STATE = {
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3,
};

function useChatWebSocket(chatId) {
    const [lastMessage, setLastMessage] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('Idle'); // Idle, Connecting, Open, Closing, Closed, Error
    const [error, setError] = useState(null);
    const ws = useRef(null);

    const connect = useCallback(() => {
        if (!chatId) {
            console.log('Chat ID is missing, cannot connect WebSocket.');
            setError('Chat ID is required to connect.');
            setConnectionStatus('Error');
            return;
        }

        // Prevent multiple connections
        if (ws.current && ws.current.readyState < WEBSOCKET_READY_STATE.CLOSING) {
            console.log(`WebSocket already connecting or open for chat ${chatId}`);
            return;
        }

        // Determine WebSocket URL (adjust protocol based on window.location)
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Assuming backend runs on the same host/port or is proxied
        // Adjust if your API/WebSocket server is elsewhere
        // Connect directly to the backend WS endpoint, bypassing Vite proxy for WS
        const backendHost = window.location.hostname; // Assuming backend is on the same host
        const backendPort = 5000; // Backend port
        const wsUrl = `${wsProtocol}//${backendHost}:${backendPort}/api/chat/ws/${chatId}`;

        console.log(`Connecting WebSocket to ${wsUrl}`);
        setConnectionStatus('Connecting');
        setError(null);

        try {
            ws.current = new WebSocket(wsUrl);

            ws.current.onopen = () => {
                console.log(`WebSocket connected for chat ${chatId}`);
                setConnectionStatus('Open');
                setError(null);
            };

            ws.current.onmessage = (event) => {
                try {
                    const messageData = JSON.parse(event.data);
                    console.log(`WebSocket message received for chat ${chatId}:`, messageData);
                    setLastMessage(messageData); // Update state with the latest message
                } catch (e) {
                    console.error('Failed to parse incoming WebSocket message:', event.data, e);
                    // Handle non-JSON messages or parsing errors if necessary
                }
            };

            ws.current.onerror = (event) => {
                console.error(`WebSocket error for chat ${chatId}:`, event);
                setError('WebSocket connection error.');
                setConnectionStatus('Error');
            };

            ws.current.onclose = (event) => {
                console.log(`WebSocket closed for chat ${chatId}. Code: ${event.code}, Reason: ${event.reason}`);
                setConnectionStatus('Closed');
                // Optionally handle specific close codes (e.g., 1008 Policy Violation for auth errors)
                if (event.code !== 1000 && event.code !== 1001) { // 1000=Normal, 1001=Going Away
                    setError(`Connection closed unexpectedly: ${event.reason || event.code}`);
                }
                ws.current = null; // Clean up ref
            };
        } catch (err) {
            console.error(`Failed to create WebSocket connection for chat ${chatId}:`, err);
            setError('Failed to establish WebSocket connection.');
            setConnectionStatus('Error');
            ws.current = null;
        }

    }, [chatId]);

    const disconnect = useCallback(() => {
        if (ws.current && ws.current.readyState === WEBSOCKET_READY_STATE.OPEN) {
            console.log(`Closing WebSocket connection for chat ${chatId}`);
            setConnectionStatus('Closing');
            ws.current.close(1000, 'User initiated disconnect'); // Normal closure
        }
        ws.current = null; // Ensure ref is cleared
    }, [chatId]);

    // Effect to connect when chatId changes and is valid
    useEffect(() => {
        if (chatId) {
            connect();
        } else {
            // If chatId becomes null/undefined, ensure disconnection
            disconnect();
        }

        // Cleanup function to close WebSocket on component unmount or chatId change
        return () => {
            disconnect();
        };
    }, [chatId, connect, disconnect]);

    const sendMessage = useCallback((messageObject) => {
        if (ws.current && ws.current.readyState === WEBSOCKET_READY_STATE.OPEN) {
            try {
                const messageString = JSON.stringify(messageObject);
                console.log(`Sending WebSocket message for chat ${chatId}:`, messageString);
                ws.current.send(messageString);
            } catch (e) {
                console.error('Failed to stringify or send WebSocket message:', e);
                setError('Failed to send message.');
            }
        } else {
            console.warn(`WebSocket not open for chat ${chatId}. Cannot send message.`);
            setError('Connection is not open. Cannot send message.');
            // Optionally try to reconnect?
            // connect();
        }
    }, [chatId]);

    return { sendMessage, lastMessage, connectionStatus, error };
}

export default useChatWebSocket;