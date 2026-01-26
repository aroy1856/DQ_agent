import type { Message } from "../types";

interface CodeMessageProps {
  message: Message;
}

export function CodeMessage({ message }: CodeMessageProps) {
  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[90%] rounded-2xl px-4 py-3 bg-white border border-indigo-100 shadow-sm">
        <p className="text-sm text-indigo-600 font-medium mb-2">
          {message.content}
        </p>
        <pre className="bg-stone-100 rounded-lg p-3 overflow-x-auto text-xs text-stone-700 font-mono max-h-80 overflow-y-auto border border-stone-200">
          <code>{message.data?.generatedCode}</code>
        </pre>
      </div>
    </div>
  );
}
