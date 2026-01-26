import type { Message } from "../types";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const { type, content, data } = message;

  return (
    <div
      className={`flex ${type === "user" ? "justify-end" : "justify-start"} mb-4`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${
          type === "user"
            ? "bg-linear-to-r from-indigo-500 to-purple-500 text-white"
            : type === "system"
              ? "bg-amber-50 border border-amber-200 text-amber-700"
              : "bg-white border border-stone-200 text-stone-700"
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{content}</p>

        {/* Summary */}
        {data?.summary && (
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="bg-stone-100 rounded-lg p-2 text-center">
              <div className="text-lg font-bold text-stone-700">
                {data.summary.total_rules}
              </div>
              <div className="text-xs text-stone-500">Total</div>
            </div>
            <div className="bg-emerald-50 rounded-lg p-2 text-center border border-emerald-200">
              <div className="text-lg font-bold text-emerald-600">
                {data.summary.passed}
              </div>
              <div className="text-xs text-emerald-500">Passed</div>
            </div>
            <div className="bg-rose-50 rounded-lg p-2 text-center border border-rose-200">
              <div className="text-lg font-bold text-rose-600">
                {data.summary.failed}
              </div>
              <div className="text-xs text-rose-500">Failed</div>
            </div>
          </div>
        )}

        {/* Errors */}
        {data?.errors && data.errors.length > 0 && (
          <div className="mt-3 p-2 bg-rose-50 rounded border border-rose-200">
            {data.errors.map((error, i) => (
              <p key={i} className="text-xs text-rose-600">
                {error}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
