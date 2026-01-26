import { useState } from "react";
import type { Message, Rule } from "../types";
import { RuleItem } from "./RuleItem";

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

  const userRules = rules.filter((r) => r.source === "user");
  const llmRules = rules.filter((r) => r.source === "llm");

  const handleEdit = (updatedRule: Rule) => {
    const updated = rules.map((r) =>
      r.id === updatedRule.id ? updatedRule : r,
    );
    setRules(updated);
    onRulesUpdate(updated);
  };

  const handleDelete = (ruleId: string) => {
    const updated = rules.filter((r) => r.id !== ruleId);
    setRules(updated);
    onRulesUpdate(updated);
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
              {userRules.map((rule, i) => (
                <RuleItem
                  key={rule.id}
                  rule={rule}
                  index={i}
                  isWaiting={isWaiting}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              ))}
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
              {llmRules.map((rule, i) => (
                <RuleItem
                  key={rule.id}
                  rule={rule}
                  index={userRules.length + i}
                  isWaiting={isWaiting}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              ))}
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
