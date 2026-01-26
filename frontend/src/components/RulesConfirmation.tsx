import { useState } from "react";
import type { Message, Rule } from "../types";

interface RulesConfirmationProps {
  message: Message;
  onConfirm: () => void;
  onCancel: () => void;
  onRulesUpdate: (rules: Rule[]) => void;
  isWaiting: boolean;
}

export function RulesConfirmation({
  message,
  onConfirm,
  onCancel,
  onRulesUpdate,
  isWaiting,
}: RulesConfirmationProps) {
  const [rules, setRules] = useState<Rule[]>(message.data?.rules || []);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const userRules = rules.filter((r) => r.source === "user");
  const llmRules = rules.filter((r) => r.source === "llm");

  const handleEdit = (rule: Rule) => {
    setEditingId(rule.id);
    setEditText(rule.text);
  };

  const handleSaveEdit = () => {
    if (!editingId) return;
    const updated = rules.map((r) =>
      r.id === editingId ? { ...r, text: editText } : r,
    );
    setRules(updated);
    onRulesUpdate(updated);
    setEditingId(null);
    setEditText("");
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditText("");
  };

  const handleDelete = (ruleId: string) => {
    const updated = rules.filter((r) => r.id !== ruleId);
    setRules(updated);
    onRulesUpdate(updated);
  };

  const renderRule = (rule: Rule, index: number) => {
    const isEditing = editingId === rule.id;

    return (
      <div
        key={rule.id}
        className={`rounded-lg p-3 border ${
          rule.source === "user"
            ? "bg-blue-50 border-blue-200"
            : "bg-purple-50 border-purple-200"
        }`}
      >
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={2}
            />
            <div className="flex gap-2">
              <button
                onClick={handleSaveEdit}
                className="px-3 py-1 text-xs bg-emerald-500 text-white rounded-md hover:bg-emerald-600"
              >
                Save
              </button>
              <button
                onClick={handleCancelEdit}
                className="px-3 py-1 text-xs bg-stone-200 text-stone-700 rounded-md hover:bg-stone-300"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1">
              <span className="text-stone-500 font-medium text-sm">
                {index + 1}.
              </span>
              <div className="flex-1">
                <p className="text-sm text-stone-700">{rule.text}</p>
                <span
                  className={`inline-block mt-1 px-2 py-0.5 text-xs rounded-full ${
                    rule.source === "user"
                      ? "bg-blue-100 text-blue-600"
                      : "bg-purple-100 text-purple-600"
                  }`}
                >
                  {rule.source === "user" ? "👤 User" : "🤖 AI"}
                </span>
              </div>
            </div>
            {isWaiting && (
              <div className="flex gap-1">
                <button
                  onClick={() => handleEdit(rule)}
                  className="p-1.5 text-stone-500 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                  title="Edit rule"
                >
                  ✏️
                </button>
                <button
                  onClick={() => handleDelete(rule.id)}
                  className="p-1.5 text-stone-500 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
                  title="Delete rule"
                >
                  🗑️
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[90%] rounded-2xl px-4 py-4 bg-white border border-indigo-200 shadow-sm">
        <p className="text-sm text-indigo-600 font-medium mb-3">
          📋 {rules.length} rules ready for review:
        </p>

        {/* User Rules */}
        {userRules.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-blue-600 mb-2">
              👤 User Rules ({userRules.length})
            </p>
            <div className="space-y-2">
              {userRules.map((rule, i) => renderRule(rule, i))}
            </div>
          </div>
        )}

        {/* AI Generated Rules */}
        {llmRules.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-purple-600 mb-2">
              🤖 AI Suggested Rules ({llmRules.length})
            </p>
            <div className="space-y-2">
              {llmRules.map((rule, i) =>
                renderRule(rule, userRules.length + i),
              )}
            </div>
          </div>
        )}

        {rules.length === 0 && (
          <p className="text-sm text-stone-500 italic">No rules to validate</p>
        )}

        {isWaiting && rules.length > 0 && (
          <div className="flex gap-2 mt-4">
            <button
              onClick={onConfirm}
              className="flex-1 py-2 px-4 rounded-lg font-medium text-white bg-indigo-500 hover:bg-indigo-600 transition-colors shadow-sm"
            >
              ✅ Proceed with {rules.length} rules
            </button>
            <button
              onClick={onCancel}
              className="py-2 px-4 rounded-lg font-medium text-stone-600 bg-stone-100 hover:bg-stone-200 border border-stone-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        )}

        {!isWaiting && (
          <p className="text-xs text-emerald-600 mt-2">
            ✓ Confirmed - proceeding with validation
          </p>
        )}
      </div>
    </div>
  );
}
