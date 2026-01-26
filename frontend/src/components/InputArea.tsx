import { useState } from "react";
import type { InputState, InputActions } from "../hooks";

interface InputAreaProps {
  state: InputState;
  actions: InputActions;
  isLoading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

export function InputArea({
  state,
  actions,
  isLoading,
  onSubmit,
  onCancel,
}: InputAreaProps) {
  const [showMetadata, setShowMetadata] = useState(false);
  const [useMetadataText, setUseMetadataText] = useState(true);

  return (
    <div className="border-t border-stone-200 bg-stone-100 px-6 py-4">
      <form onSubmit={onSubmit} className="max-w-4xl mx-auto">
        <div className="flex flex-wrap gap-3 mb-3">
          {/* CSV Upload */}
          <div className="flex items-center gap-2">
            <input
              type="file"
              accept=".csv"
              id="csv-upload"
              className="hidden"
              onChange={(e) => actions.setCsvFile(e.target.files?.[0] || null)}
            />
            <label
              htmlFor="csv-upload"
              className="cursor-pointer px-4 py-2 rounded-lg bg-white border border-stone-300 hover:border-indigo-300 hover:bg-indigo-50 text-sm text-stone-700 transition-colors flex items-center gap-2 shadow-sm"
            >
              {state.csvFile ? state.csvFile.name : "Select CSV"}
            </label>
          </div>

          {/* Rules Toggle */}
          <div className="flex items-center gap-1 bg-white rounded-lg p-1 border border-stone-300 shadow-sm">
            <button
              type="button"
              onClick={() => actions.setUseTextRules(false)}
              className={`px-3 py-1.5 rounded-md text-xs transition-colors ${
                !state.useTextRules
                  ? "bg-indigo-500 text-white"
                  : "text-stone-500 hover:text-stone-700"
              }`}
            >
              File
            </button>
            <button
              type="button"
              onClick={() => actions.setUseTextRules(true)}
              className={`px-3 py-1.5 rounded-md text-xs transition-colors ${
                state.useTextRules
                  ? "bg-indigo-500 text-white"
                  : "text-stone-500 hover:text-stone-700"
              }`}
            >
              Text
            </button>
          </div>

          {/* Rules File Upload */}
          {!state.useTextRules && (
            <div className="flex items-center gap-2">
              <input
                type="file"
                accept=".txt"
                id="rules-upload"
                className="hidden"
                onChange={(e) =>
                  actions.setRulesFile(e.target.files?.[0] || null)
                }
              />
              <label
                htmlFor="rules-upload"
                className="cursor-pointer px-4 py-2 rounded-lg bg-white border border-stone-300 hover:border-indigo-300 hover:bg-indigo-50 text-sm text-stone-700 transition-colors flex items-center gap-2 shadow-sm"
              >
                {state.rulesFile ? state.rulesFile.name : "Select Rules"}
              </label>
            </div>
          )}

          {/* Metadata Toggle */}
          <button
            type="button"
            onClick={() => setShowMetadata(!showMetadata)}
            className={`px-4 py-2 rounded-lg text-sm transition-colors flex items-center gap-2 shadow-sm ${
              showMetadata || state.metadata || state.metadataFile
                ? "bg-emerald-50 border border-emerald-300 text-emerald-700"
                : "bg-white border border-stone-300 text-stone-700 hover:border-emerald-300 hover:bg-emerald-50"
            }`}
          >
            {state.metadata || state.metadataFile
              ? "Metadata Added"
              : "Add Metadata"}
          </button>
        </div>

        {/* Text Rules Input */}
        {state.useTextRules && (
          <textarea
            value={state.rulesText}
            onChange={(e) => actions.setRulesText(e.target.value)}
            rows={2}
            placeholder="Enter rules (one per line)..."
            className="w-full mb-3 px-4 py-2 rounded-lg bg-white border border-stone-300 text-stone-700 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm resize-none shadow-sm"
          />
        )}

        {/* Column Metadata Input */}
        {showMetadata && (
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-stone-500">
                Column Metadata (helps AI generate better rules & code)
              </label>
              <div className="flex items-center gap-1 bg-white rounded-lg p-0.5 border border-stone-300">
                <button
                  type="button"
                  onClick={() => setUseMetadataText(true)}
                  className={`px-2 py-1 rounded text-xs transition-colors ${
                    useMetadataText
                      ? "bg-emerald-500 text-white"
                      : "text-stone-500 hover:text-stone-700"
                  }`}
                >
                  Text
                </button>
                <button
                  type="button"
                  onClick={() => setUseMetadataText(false)}
                  className={`px-2 py-1 rounded text-xs transition-colors ${
                    !useMetadataText
                      ? "bg-emerald-500 text-white"
                      : "text-stone-500 hover:text-stone-700"
                  }`}
                >
                  File
                </button>
              </div>
            </div>
            {useMetadataText ? (
              <textarea
                value={state.metadata}
                onChange={(e) => actions.setMetadata(e.target.value)}
                rows={3}
                placeholder={`Describe your columns, e.g.:
- id: unique identifier, should never be null
- email: user email, must be valid format
- age: integer between 0-120
- amount: transaction amount in USD, no negatives
- status: enum (active, inactive, pending)`}
                className="w-full px-4 py-2 rounded-lg bg-white border border-emerald-200 text-stone-700 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm resize-none shadow-sm"
              />
            ) : (
              <div className="flex items-center gap-2">
                <input
                  type="file"
                  accept=".txt,.md"
                  id="metadata-upload"
                  className="hidden"
                  onChange={(e) =>
                    actions.setMetadataFile(e.target.files?.[0] || null)
                  }
                />
                <label
                  htmlFor="metadata-upload"
                  className="cursor-pointer px-4 py-2 rounded-lg bg-white border border-emerald-200 hover:border-emerald-400 hover:bg-emerald-50 text-sm text-stone-700 transition-colors flex items-center gap-2 shadow-sm"
                >
                  {state.metadataFile
                    ? state.metadataFile.name
                    : "Select Metadata File"}
                </label>
                {state.metadataFile && (
                  <button
                    type="button"
                    onClick={() => actions.setMetadataFile(null)}
                    className="text-stone-400 hover:text-rose-500"
                  >
                    ×
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Submit */}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 py-3 rounded-xl font-medium text-white bg-linear-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
          >
            {isLoading ? "Processing..." : "Run DQ Check"}
          </button>
          {isLoading && (
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-3 rounded-xl bg-white border border-stone-300 hover:bg-stone-50 text-stone-700 transition-colors shadow-sm"
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
