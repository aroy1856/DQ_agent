import { useState, useRef, useCallback } from "react";
import type { Message, Rule } from "../types";

type StreamPhase =
  | "idle"
  | "creating"
  | "loading"
  | "waiting_confirmation"
  | "generating"
  | "complete";

export function useDQStream() {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState("");
  const [phase, setPhase] = useState<StreamPhase>("idle");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [pendingConfirmationId, setPendingConfirmationId] = useState<
    string | null
  >(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const runDQCheck = useCallback(
    async (
      csvFile: File,
      rulesFile: File | null,
      rulesText: string,
      useTextRules: boolean,
      metadata: string,
      metadataFile: File | null,
      addMessage: (msg: Omit<Message, "id" | "timestamp">) => string,
    ) => {
      setIsLoading(true);
      setPhase("creating");
      setCurrentStep("Creating conversation thread...");

      try {
        // Create thread
        const createRes = await fetch("/api/thread/create", { method: "POST" });
        if (!createRes.ok) throw new Error("Failed to create thread");
        const { thread_id } = await createRes.json();
        setThreadId(thread_id);

        // Load rules
        setPhase("loading");
        setCurrentStep("Loading data and generating AI suggestions...");

        const formData = new FormData();
        formData.append("csv_file", csvFile);

        if (useTextRules && rulesText.trim()) {
          const rules = rulesText.split("\n").filter((r) => r.trim());
          formData.append("rules", JSON.stringify(rules));
        } else if (rulesFile) {
          formData.append("rules_file", rulesFile);
        }

        // Add metadata (text or file)
        if (metadataFile) {
          formData.append("metadata_file", metadataFile);
        } else if (metadata.trim()) {
          formData.append("metadata", metadata.trim());
        }
        // If no rules provided, still continue - AI will generate suggestions

        const loadRes = await fetch(`/api/thread/${thread_id}/load-rules`, {
          method: "POST",
          body: formData,
        });

        if (!loadRes.ok) {
          const error = await loadRes.json();
          throw new Error(error.detail || "Failed to load rules");
        }

        const rulesData = await loadRes.json();

        // Show rules for confirmation
        setPhase("waiting_confirmation");
        setCurrentStep("");
        setIsLoading(false);

        const confirmMsgId = addMessage({
          type: "confirmation",
          content: "Rules loaded - please review and confirm",
          data: { rules: rulesData.rules },
        });
        setPendingConfirmationId(confirmMsgId);
      } catch (error) {
        setIsLoading(false);
        setPhase("idle");
        if (error instanceof Error) {
          addMessage({
            type: "system",
            content: `Error: ${error.message}`,
          });
        }
      }
    },
    [],
  );

  const updateRules = useCallback(
    async (rules: Rule[]) => {
      if (!threadId) return;

      try {
        await fetch(`/api/thread/${threadId}/rules`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rules }),
        });
      } catch (error) {
        console.error("Failed to update rules:", error);
      }
    },
    [threadId],
  );

  const confirmRules = useCallback(
    async (addMessage: (msg: Omit<Message, "id" | "timestamp">) => string) => {
      if (!threadId) return;

      setIsLoading(true);
      setPhase("generating");
      setCurrentStep("Generating validation code...");
      setPendingConfirmationId(null);

      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch(`/api/thread/${threadId}/confirm`, {
          method: "POST",
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("No response body");
        }

        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let eventType = "";
          let eventData = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7);
            } else if (line.startsWith("data: ")) {
              eventData = line.slice(6);

              if (eventType && eventData) {
                try {
                  const data = JSON.parse(eventData);

                  switch (eventType) {
                    case "status":
                      setCurrentStep(data.message);
                      break;

                    case "code_generated":
                      addMessage({
                        type: "code",
                        content: "Generated validation code:",
                        data: { generatedCode: data.generated_code },
                      });
                      break;

                    case "code_executed":
                      addMessage({
                        type: "results",
                        content: "Execution results:",
                        data: { results: data.execution_results },
                      });
                      break;

                    case "complete":
                      setPhase("complete");
                      addMessage({
                        type: "assistant",
                        content: "DQ Check Complete!",
                        data: { summary: data.summary, errors: data.errors },
                      });
                      break;

                    case "error":
                      addMessage({
                        type: "system",
                        content: `Error: ${data.error}`,
                        data: { errors: [data.error] },
                      });
                      break;
                  }
                } catch {
                  console.error("Failed to parse event data:", eventData);
                }
                eventType = "";
                eventData = "";
              }
            }
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name !== "AbortError") {
          addMessage({
            type: "system",
            content: `Error: ${error.message}`,
          });
        }
      } finally {
        setIsLoading(false);
        setCurrentStep("");
        setPhase("idle");
        setThreadId(null);
      }
    },
    [threadId],
  );

  const cancel = useCallback(async () => {
    abortControllerRef.current?.abort();

    if (threadId) {
      try {
        await fetch(`/api/thread/${threadId}`, { method: "DELETE" });
      } catch {
        // Ignore cleanup errors
      }
    }

    setIsLoading(false);
    setCurrentStep("");
    setPhase("idle");
    setThreadId(null);
    setPendingConfirmationId(null);
  }, [threadId]);

  return {
    isLoading,
    currentStep,
    phase,
    threadId,
    pendingConfirmationId,
    runDQCheck,
    updateRules,
    confirmRules,
    cancel,
  };
}
