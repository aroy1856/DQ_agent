import { useState } from "react";
import type { Rule } from "../types";

interface RuleItemProps {
  rule: Rule;
  index: number;
  isWaiting: boolean;
  onEdit: (rule: Rule) => void;
  onDelete: (ruleId: string) => void;
}

export function RuleItem({
  rule,
  index,
  isWaiting,
  onEdit,
  onDelete,
}: RuleItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(rule.text);

  const handleSave = () => {
    onEdit({ ...rule, text: editText });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditText(rule.text);
    setIsEditing(false);
  };

  return (
    <div
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
            autoFocus
          />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="px-3 py-1 text-xs bg-emerald-500 text-white rounded-md hover:bg-emerald-600"
            >
              Save
            </button>
            <button
              onClick={handleCancel}
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
                onClick={() => setIsEditing(true)}
                className="p-1.5 text-stone-500 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                title="Edit rule"
              >
                ✏️
              </button>
              <button
                onClick={() => onDelete(rule.id)}
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
}
