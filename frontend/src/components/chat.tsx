"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Send,
  Bot,
  User,
  Mail,
  MessageSquare,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface EmailSource {
  email_id: string;
  thread_id: string;
  subject: string;
  from_address: string;
  from_name: string;
  sent_at: string;
}

interface ChatMessage {
  id: string;
  type: "user" | "assistant";
  content: string;
  sources?: EmailSource[];
  timestamp: Date;
}

interface ChatProps {
  onEmailSelect?: (threadId: string) => void;
}

export function Chat({ onEmailSelect }: ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatStatus, setChatStatus] = useState<{
    indexed_emails: number;
    ai_enabled: boolean;
    status: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Check chat status on component mount
    checkChatStatus();
  }, []);

  const checkChatStatus = async () => {
    try {
      const response = await fetch("http://localhost:8000/chat/status", {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const status = await response.json();
        setChatStatus(status);

        if (status.indexed_emails === 0) {
          // Try to index emails
          await indexEmails();
        }
      }
    } catch (error) {
      console.error("Error checking chat status:", error);
      setError("Failed to check chat status");
    }
  };

  const indexEmails = async () => {
    try {
      const response = await fetch("http://localhost:8000/chat/index", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        // Refresh status after indexing
        await checkChatStatus();
      }
    } catch (error) {
      console.error("Error indexing emails:", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/chat/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: data.response,
        sources: data.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      setError("Failed to send message. Please try again.");

      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content:
          "Sorry, I encountered an error while processing your request. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const isReady = chatStatus?.status === "ready";

  return (
    <Card className="flex flex-col h-full max-h-screen">
      <CardHeader className="flex-shrink-0 pb-2">
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Email Assistant
          {chatStatus && (
            <Badge
              variant={isReady ? "default" : "secondary"}
              className="ml-auto"
            >
              {chatStatus.indexed_emails} emails indexed
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col flex-1 min-h-0 p-0">
        {error && (
          <Alert className="mx-4 mb-4" variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {!isReady && (
          <Alert className="mx-4 mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {!chatStatus?.ai_enabled
                ? "AI service is not configured. Please add your OpenAI API key to enable chat functionality."
                : chatStatus?.indexed_emails === 0
                ? "Indexing your emails for chat... This may take a moment."
                : "Chat service is not ready yet."}
            </AlertDescription>
          </Alert>
        )}

        <ScrollArea
          className="flex-1 min-h-0 overflow-y-auto"
          ref={scrollAreaRef}
        >
          <div className="p-4 min-h-full">
            <div className="space-y-4 min-h-full">
              {messages.length === 0 && (
                <div className="text-center text-muted-foreground py-8">
                  <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Ask me anything about your emails!</p>
                  <div className="text-sm mt-2 space-y-1">
                    <p>Try asking:</p>
                    <div className="space-y-1">
                      <p>• "Show me emails from last week"</p>
                      <p>• "Find emails about project updates"</p>
                      <p>• "What are my unread emails about?"</p>
                      <p>• "Summarize my emails from today"</p>
                    </div>
                  </div>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.type === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`flex gap-3 max-w-[80%] ${
                      message.type === "user" ? "flex-row-reverse" : "flex-row"
                    }`}
                  >
                    <div className="flex-shrink-0">
                      {message.type === "user" ? (
                        <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center">
                          <User className="h-4 w-4" />
                        </div>
                      ) : (
                        <div className="w-8 h-8 bg-muted text-muted-foreground rounded-full flex items-center justify-center">
                          <Bot className="h-4 w-4" />
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-2">
                      <div
                        className={`rounded-lg p-3 ${
                          message.type === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">
                          {message.content}
                        </p>
                      </div>

                      {message.sources && message.sources.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs text-muted-foreground">
                            Related emails:
                          </p>
                          {message.sources.map((source, index) => (
                            <Button
                              key={index}
                              variant="outline"
                              size="sm"
                              className="justify-start h-auto p-2 text-xs w-full hover:bg-accent cursor-pointer"
                              onClick={() => {
                                console.log("Clicked source:", source);
                                console.log("Thread ID:", source.thread_id);
                                onEmailSelect?.(source.thread_id);
                              }}
                              title="Click to view this email (may require loading)"
                            >
                              <Mail className="h-3 w-3 mr-2 flex-shrink-0" />
                              <div className="text-left min-w-0 flex-1">
                                <div className="font-medium truncate">
                                  {source.subject}
                                </div>
                                <div className="text-muted-foreground">
                                  From:{" "}
                                  {source.from_name || source.from_address}
                                </div>
                                <div className="text-muted-foreground">
                                  {formatDate(source.sent_at)}
                                </div>
                              </div>
                            </Button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 bg-muted text-muted-foreground rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-muted rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        </ScrollArea>

        <div className="border-t p-4 flex-shrink-0 bg-background">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                isReady ? "Ask about your emails..." : "Chat not ready..."
              }
              disabled={isLoading || !isReady}
              className="flex-1"
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading || !isReady}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          {isReady && (
            <p className="text-xs text-muted-foreground mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
