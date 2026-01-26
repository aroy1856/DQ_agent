interface InputAreaProps {
  csvFile: File | null;
  setCsvFile: (file: File | null) => void;
  rulesFile: File | null;
  setRulesFile: (file: File | null) => void;
  rulesText: string;
  setRulesText: (text: string) => void;
  useTextRules: boolean;
  setUseTextRules: (use: boolean) => void;
  isLoading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

export function InputArea({
  csvFile,
  setCsvFile,
  rulesFile,
  setRulesFile,
  rulesText,
  setRulesText,
  useTextRules,
  setUseTextRules,
  isLoading,
  onSubmit,
  onCancel,
}: InputAreaProps) {
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
              onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
            />
            <label
              htmlFor="csv-upload"
              className="cursor-pointer px-4 py-2 rounded-lg bg-white border border-stone-300 hover:border-indigo-300 hover:bg-indigo-50 text-sm text-stone-700 transition-colors flex items-center gap-2 shadow-sm"
            >
              📊 {csvFile ? csvFile.name : "Select CSV"}
            </label>
          </div>

          {/* Rules Toggle */}
          <div className="flex items-center gap-1 bg-white rounded-lg p-1 border border-stone-300 shadow-sm">
            <button
              type="button"
              onClick={() => setUseTextRules(false)}
              className={`px-3 py-1.5 rounded-md text-xs transition-colors ${
                !useTextRules
                  ? "bg-indigo-500 text-white"
                  : "text-stone-500 hover:text-stone-700"
              }`}
            >
              File
            </button>
            <button
              type="button"
              onClick={() => setUseTextRules(true)}
              className={`px-3 py-1.5 rounded-md text-xs transition-colors ${
                useTextRules
                  ? "bg-indigo-500 text-white"
                  : "text-stone-500 hover:text-stone-700"
              }`}
            >
              Text
            </button>
          </div>

          {/* Rules File Upload */}
          {!useTextRules && (
            <div className="flex items-center gap-2">
              <input
                type="file"
                accept=".txt"
                id="rules-upload"
                className="hidden"
                onChange={(e) => setRulesFile(e.target.files?.[0] || null)}
              />
              <label
                htmlFor="rules-upload"
                className="cursor-pointer px-4 py-2 rounded-lg bg-white border border-stone-300 hover:border-indigo-300 hover:bg-indigo-50 text-sm text-stone-700 transition-colors flex items-center gap-2 shadow-sm"
              >
                📝 {rulesFile ? rulesFile.name : "Select Rules"}
              </label>
            </div>
          )}
        </div>

        {/* Text Rules Input */}
        {useTextRules && (
          <textarea
            value={rulesText}
            onChange={(e) => setRulesText(e.target.value)}
            rows={2}
            placeholder="Enter rules (one per line)..."
            className="w-full mb-3 px-4 py-2 rounded-lg bg-white border border-stone-300 text-stone-700 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm resize-none shadow-sm"
          />
        )}

        {/* Submit */}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 py-3 rounded-xl font-medium text-white bg-linear-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
          >
            {isLoading ? "⏳ Processing..." : "🚀 Run DQ Check"}
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
