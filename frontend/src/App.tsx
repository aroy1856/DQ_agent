import { useState, useRef, useEffect, useCallback } from "react";
import "./App.css";
import type { Message, Rule } from "./types";
import {
  ChatMessage,
  CodeMessage,
  ResultsMessage,
  InputArea,
  RulesConfirmation,
} from "./components";
import { useDQStream, useInputState } from "./hooks";

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "assistant",
      content:
        "Welcome to DQ Agent! Upload a CSV file and rules to validate your data quality. I will also suggest additional rules based on your data.",
      timestamp: new Date(),
    },
  ]);

  // Use reducer-based input state management
  const { state: inputState, actions: inputActions } = useInputState();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    isLoading,
    currentStep,
    phase,
    pendingConfirmationId,
    runDQCheck,
    updateRules,
    confirmRules,
    cancel,
  } = useDQStream();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = useCallback(
    (message: Omit<Message, "id" | "timestamp">): string => {
      const newMessage: Message = {
        ...message,
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, newMessage]);
      return newMessage.id;
    },
    [],
  );

  const updateMessage = useCallback((id: string, updates: Partial<Message>) => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === id ? { ...msg, ...updates } : msg)),
    );
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputState.csvFile) {
      addMessage({ type: "system", content: "Please select a CSV file" });
      return;
    }

    addMessage({
      type: "user",
      content: `Run DQ check on ${inputState.csvFile.name}`,
    });

    await runDQCheck(
      inputState.csvFile,
      inputState.rulesFile,
      inputState.rulesText,
      inputState.useTextRules,
      inputState.metadata,
      inputState.metadataFile,
      addMessage,
    );
  };

  const handleCancel = async () => {
    await cancel();
    addMessage({ type: "system", content: "Request cancelled" });
  };

  const handleRulesUpdate = (rules: Rule[]) => {
    updateRules(rules);
    if (pendingConfirmationId) {
      updateMessage(pendingConfirmationId, {
        data: { rules },
      });
    }
  };

  const handleConfirmRules = async () => {
    addMessage({
      type: "user",
      content: "Proceed with validation",
    });

    if (pendingConfirmationId) {
      updateMessage(pendingConfirmationId, {
        content: "Rules confirmed",
      });
    }
    await confirmRules(addMessage);
  };

  const renderMessage = (message: Message) => {
    switch (message.type) {
      case "code":
        return <CodeMessage message={message} />;
      case "results":
        return <ResultsMessage message={message} />;
      case "confirmation":
        return (
          <RulesConfirmation
            message={message}
            onConfirm={handleConfirmRules}
            onCancel={handleCancel}
            onRulesUpdate={handleRulesUpdate}
            isWaiting={
              phase === "waiting_confirmation" &&
              message.id === pendingConfirmationId
            }
          />
        );
      default:
        return <ChatMessage message={message} />;
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col">
      {/* Header */}
      <header className="border-b border-stone-200 bg-white px-6 py-4 shadow-sm">
        <h1 className="text-2xl font-bold text-indigo-600">DQ Agent</h1>
        <p className="text-sm text-stone-500">
          AI-Powered Data Quality Validation
        </p>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto">
          {messages.map((message) => (
            <div key={message.id}>{renderMessage(message)}</div>
          ))}
          {isLoading && phase !== "waiting_confirmation" && (
            <div className="flex justify-start mb-4">
              <div className="bg-white border border-stone-200 rounded-2xl px-4 py-3 text-stone-600 flex items-center gap-2 shadow-sm">
                <svg
                  className="animate-spin h-4 w-4 text-indigo-500"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <span className="text-sm">
                  {currentStep || "Processing..."}
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <InputArea
        state={inputState}
        actions={inputActions}
        isLoading={isLoading || phase === "waiting_confirmation"}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
      />
    </div>
  );
}

export default App;
