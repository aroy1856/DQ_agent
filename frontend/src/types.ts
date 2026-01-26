export interface DQResult {
  rule: string;
  passed: boolean;
  details: string;
}

export interface Rule {
  id: string;
  text: string;
  source: "user" | "llm";
}

export interface Message {
  id: string;
  type: "user" | "assistant" | "system" | "code" | "results" | "confirmation";
  content: string;
  timestamp: Date;
  data?: MessageData;
}

export interface MessageData {
  csvFileName?: string;
  rulesFileName?: string;
  rules?: Rule[];
  generatedCode?: string;
  results?: DQResult[];
  summary?: { total_rules: number; passed: number; failed: number };
  errors?: string[];
}
