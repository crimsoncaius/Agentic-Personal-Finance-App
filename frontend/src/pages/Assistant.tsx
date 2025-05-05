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

// Component for individual chat messages
const ChatMessage = ({ message }: { message: Message }) => {
  const isUser = message.sender === "user";

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
                amount,
                date,
                description,
                isRecurring,
                recurrencePeriod,
                type,
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
        {message.data && formatDataTable(message.data)}
      </div>
    </div>
  );
};

// Main Assistant component
const Assistant = () => {
  const [messages, setMessages] = useState<Message[]>(() => {
    // Initialize messages from localStorage or default message
    const savedMessages = localStorage.getItem("chatMessages");
    if (savedMessages) {
      return deserializeMessages(savedMessages);
    }
    return [
      {
        id: "1",
        content:
          "Hello! I'm your financial assistant. How can I help you today?",
        sender: "assistant",
        timestamp: new Date(),
      },
    ];
  });

  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem("chatMessages", serializeMessages(messages));
  }, [messages]);

  // Automatically scroll to the bottom of the chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Function to send messages to the backend
  const sendMessage = async () => {
    if (inputValue.trim() === "") return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await apiService.sendChatMessage(userMessage.content);

      const assistantMessage: Message = {
        id: Date.now().toString(),
        content: response.response || "Sorry, I couldn't process that request.",
        sender: "assistant",
        timestamp: new Date(),
        isError: !response.success,
        data: response.data,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        content:
          error.response?.data?.detail ||
          error.message ||
          "An error occurred while processing your request.",
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
      sendMessage();
    }
  };

  const resetChat = async () => {
    try {
      const response = await apiService.resetChat();
      const newMessages: Message[] = [
        {
          id: "1",
          content: response.response,
          sender: "assistant" as const,
          timestamp: new Date(),
        },
      ];
      setMessages(newMessages);
      localStorage.setItem("chatMessages", serializeMessages(newMessages));
    } catch (error) {
      console.error("Error resetting chat:", error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        content:
          "Sorry, I encountered an error while resetting the chat. Please try again.",
        sender: "assistant",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/wav",
        });
        const audioFile = new File([audioBlob], "recording.wav", {
          type: "audio/wav",
        });

        setIsLoading(true);
        try {
          const transcription = await apiService.transcribeAudio(audioFile);

          // First add the transcribed text as user message
          const userMessage: Message = {
            id: Date.now().toString(),
            content: transcription.text,
            sender: "user",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, userMessage]);

          // Then get AI's response to the transcribed text
          const aiResponse = await apiService.sendChatMessage(
            transcription.text
          );

          const assistantMessage: Message = {
            id: Date.now().toString(),
            content:
              aiResponse.response || "Sorry, I couldn't process that audio.",
            sender: "assistant",
            timestamp: new Date(),
            isError: !aiResponse.success,
            data: aiResponse.data,
          };

          setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
          console.error("Error processing audio:", error);
          const errorMessage: Message = {
            id: Date.now().toString(),
            content:
              "Sorry, I encountered an error processing your audio. Please try again.",
            sender: "assistant",
            timestamp: new Date(),
            isError: true,
          };
          setMessages((prev) => [...prev, errorMessage]);
        } finally {
          setIsLoading(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        content:
          "Sorry, I couldn't access your microphone. Please check your permissions and try again.",
        sender: "assistant",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
      setIsRecording(false);
    }
  };

  return (
    <div className="flex flex-col h-[85vh]">
      <div className="bg-white p-6 rounded-lg shadow-md flex-1 flex flex-col">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-xl font-semibold">Financial Assistant</h1>
          <button
            onClick={resetChat}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none"
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
            <span>New Chat</span>
          </button>
        </div>

        {/* Chat messages container */}
        <div className="flex-1 overflow-y-auto mb-4 pr-2">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="mt-auto">
          <div className="flex items-center bg-gray-50 rounded-lg border border-gray-300">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me about your finances..."
              className="flex-1 p-3 bg-transparent outline-none resize-none"
              rows={2}
              disabled={isLoading || isRecording}
            />
            <div className="flex items-center space-x-2 pr-2">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isLoading}
                className={`p-2 rounded-lg focus:outline-none ${
                  isRecording
                    ? "bg-red-500 hover:bg-red-600"
                    : "bg-blue-500 hover:bg-blue-600"
                } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
                title={isRecording ? "Stop Recording" : "Start Recording"}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  {isRecording ? (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  ) : (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                    />
                  )}
                </svg>
              </button>
              <button
                onClick={sendMessage}
                disabled={isLoading || inputValue.trim() === "" || isRecording}
                className="px-4 py-2 bg-blue-500 text-white rounded-r-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <span className="inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                ) : (
                  "Send"
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Assistant;
