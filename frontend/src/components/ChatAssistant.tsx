import { useState, useRef, useEffect } from "react";
import apiService from "../api/api";

// Types for the chat interface
interface Message {
  id: string;
  content: string;
  sender: "user" | "assistant";
  timestamp: Date;
  isError?: boolean;
  data?: any;
}

// Component for individual chat messages
const ChatMessage = ({ message }: { message: Message }) => {
  const isUser = message.sender === "user";

  // Function to format category data
  const formatCategories = (data: any[]) => {
    console.log("Formatting categories data:", data);
    if (!data || !Array.isArray(data) || data.length === 0) {
      console.log("No data to format");
      return null;
    }

    // Check if the data is in category format (has name and type properties)
    const isCategories = data[0] && "name" in data[0] && "type" in data[0];
    console.log("Is category data:", isCategories);

    if (!isCategories) {
      console.log("Not category data, falling back to transaction table");
      return formatDataTable(data); // Fall back to transaction table format
    }

    return (
      <div className="mt-2 overflow-x-auto bg-white rounded-lg shadow">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category Name
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.map((category, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-4 py-2 whitespace-nowrap">
                  <span className="font-medium text-gray-900">
                    {category.name}
                  </span>
                </td>
                <td className="px-4 py-2 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      category.type === "EXPENSE"
                        ? "bg-red-100 text-red-800"
                        : "bg-green-100 text-green-800"
                    }`}
                  >
                    {category.type}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Function to format data tables from the assistant's response
  const formatDataTable = (data: any[]) => {
    if (!data || data.length === 0) return null;

    return (
      <div className="mt-2 overflow-x-auto bg-white rounded-lg shadow">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <tbody className="divide-y divide-gray-200">
            {data.map((row, rowIndex) => {
              if (!Array.isArray(row)) return null;

              // Skip rows that don't have enough data
              if (row.length < 3) return null;

              const [
                id,
                amount,
                date,
                description,
                isRecurring,
                recurrencePeriod,
                type,
                categoryId,
              ] = row;
              const isExpense = type === "EXPENSE";

              return (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex flex-col">
                      <span className="font-medium text-gray-900">
                        {description || "No description"}
                      </span>
                      {isRecurring === "1" && (
                        <span className="text-xs text-indigo-600">
                          Recurring ({recurrencePeriod.toLowerCase()})
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-sm">
                      {new Date(date).toLocaleDateString("en-US", {
                        weekday: "short",
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <span
                      className={`font-medium ${
                        isExpense ? "text-red-600" : "text-green-600"
                      }`}
                    >
                      {isExpense ? "-" : "+"}$
                      {Number(amount).toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        isExpense
                          ? "bg-red-100 text-red-800"
                          : "bg-green-100 text-green-800"
                      }`}
                    >
                      {type.charAt(0) + type.slice(1).toLowerCase()}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-3/4 rounded-lg px-4 py-3 ${
          isUser
            ? "bg-blue-500 text-white"
            : message.isError
            ? "bg-red-100 text-red-700 border border-red-300"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.data && <div>{formatCategories(message.data)}</div>}
      </div>
    </div>
  );
};

// Function to serialize messages for localStorage
const serializeMessages = (messages: Message[]): string => {
  return JSON.stringify(
    messages.map((msg) => ({
      ...msg,
      timestamp: msg.timestamp.toISOString(),
    }))
  );
};

// Function to deserialize messages from localStorage
const deserializeMessages = (data: string): Message[] => {
  try {
    const parsed = JSON.parse(data);
    return parsed.map((msg: any) => ({
      ...msg,
      timestamp: new Date(msg.timestamp),
    }));
  } catch (error) {
    console.error("Error deserializing messages:", error);
    return [];
  }
};

// Main ChatAssistant component - floating version
const ChatAssistant = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>(() => {
    // Initialize messages from localStorage or default message
    const savedMessages = localStorage.getItem("floatingChatMessages");
    if (savedMessages) {
      return deserializeMessages(savedMessages);
    }
    return [
      {
        id: "1",
        content:
          "Hello! I'm your financial assistant. How can I help you today?",
        sender: "assistant" as const,
        timestamp: new Date(),
      },
    ];
  });
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  // Automatically scroll to the bottom of the chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Add click outside listener to close the chat
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        chatRef.current &&
        !chatRef.current.contains(event.target as Node) &&
        isOpen
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem("floatingChatMessages", serializeMessages(messages));
  }, [messages]);

  // Function to send messages to the backend
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      console.log("Sending message:", userMessage.content);
      const response = await apiService.sendChatMessage(userMessage.content);
      console.log("Received response:", response);

      if (response.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: response.response,
          sender: "assistant",
          timestamp: new Date(),
          data: response.data,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        throw new Error(response.error || "Failed to get response");
      }
    } catch (error: any) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content:
          error.response?.data?.detail ||
          error.message ||
          "Sorry, I encountered an error. Please try again.",
        sender: "assistant",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle enter key press
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  const handleReset = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.resetChat();
      if (response.success) {
        setMessages([]);
        localStorage.removeItem("floatingChatMessages");
        setInputValue("");
      } else {
        console.error("Failed to reset chat:", response.error);
      }
    } catch (error) {
      console.error("Error resetting chat:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50" ref={chatRef}>
      {/* Floating chat button */}
      <button
        className="w-14 h-14 rounded-full bg-blue-500 text-white flex items-center justify-center shadow-lg hover:bg-blue-600 focus:outline-none"
        onClick={toggleChat}
      >
        {isOpen ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            className="w-6 h-6"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            className="w-6 h-6"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        )}
      </button>

      {/* Chat drawer */}
      {isOpen && (
        <div className="absolute bottom-16 right-0 w-80 sm:w-96 h-96 bg-white rounded-lg shadow-xl overflow-hidden flex flex-col">
          <div className="bg-blue-500 text-white px-4 py-3 flex justify-between items-center">
            <h3 className="font-medium">Financial Assistant</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleReset}
                disabled={isLoading}
                className="text-white hover:text-gray-200 focus:outline-none"
                title="Reset Chat"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </button>
              <button
                onClick={toggleChat}
                className="text-white hover:text-gray-200 focus:outline-none"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Chat messages */}
          <div className="flex-1 overflow-y-auto p-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-gray-200 p-2">
            <div className="flex items-center bg-gray-50 rounded-lg border border-gray-300">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me about your finances..."
                className="flex-1 p-2 bg-transparent outline-none resize-none text-sm"
                rows={2}
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={isLoading || inputValue.trim() === ""}
                className="px-3 py-1 bg-blue-500 text-white rounded-r-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatAssistant;
