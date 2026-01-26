import type { Message } from "../types";

interface ResultsMessageProps {
  message: Message;
}

export function ResultsMessage({ message }: ResultsMessageProps) {
  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[90%] rounded-2xl px-4 py-3 bg-white border border-stone-200 shadow-sm">
        <p className="text-sm text-stone-600 font-medium mb-3">
          {message.content}
        </p>
        <div className="space-y-2">
          {message.data?.results?.map((result, i) => (
            <div
              key={i}
              className={`rounded-lg p-3 border ${
                result.passed
                  ? "bg-emerald-50 border-emerald-200"
                  : "bg-rose-50 border-rose-200"
              }`}
            >
              <div className="flex items-start gap-2">
                <span>{result.passed ? "PASS" : "FAIL"}</span>
                <div>
                  <p className="text-sm font-medium text-stone-700">
                    {result.rule}
                  </p>
                  <p
                    className={`text-xs mt-1 ${result.passed ? "text-emerald-600" : "text-rose-600"}`}
                  >
                    {result.details}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
