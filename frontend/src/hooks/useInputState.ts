import { useReducer, useCallback } from "react";

// State type
export interface InputState {
  csvFile: File | null;
  rulesFile: File | null;
  rulesText: string;
  useTextRules: boolean;
  metadata: string;
  metadataFile: File | null;
}

// Actions type (for passing to components)
export interface InputActions {
  setCsvFile: (file: File | null) => void;
  setRulesFile: (file: File | null) => void;
  setRulesText: (text: string) => void;
  setUseTextRules: (use: boolean) => void;
  setMetadata: (text: string) => void;
  setMetadataFile: (file: File | null) => void;
  reset: () => void;
}

// Action types
type InputAction =
  | { type: "SET_CSV_FILE"; payload: File | null }
  | { type: "SET_RULES_FILE"; payload: File | null }
  | { type: "SET_RULES_TEXT"; payload: string }
  | { type: "SET_USE_TEXT_RULES"; payload: boolean }
  | { type: "SET_METADATA"; payload: string }
  | { type: "SET_METADATA_FILE"; payload: File | null }
  | { type: "RESET" };

// Initial state
const initialState: InputState = {
  csvFile: null,
  rulesFile: null,
  rulesText: "",
  useTextRules: false,
  metadata: "",
  metadataFile: null,
};

// Reducer function
function inputReducer(state: InputState, action: InputAction): InputState {
  switch (action.type) {
    case "SET_CSV_FILE":
      return { ...state, csvFile: action.payload };
    case "SET_RULES_FILE":
      return { ...state, rulesFile: action.payload };
    case "SET_RULES_TEXT":
      return { ...state, rulesText: action.payload };
    case "SET_USE_TEXT_RULES":
      return { ...state, useTextRules: action.payload };
    case "SET_METADATA":
      return { ...state, metadata: action.payload };
    case "SET_METADATA_FILE":
      return { ...state, metadataFile: action.payload };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

// Custom hook
export function useInputState() {
  const [state, dispatch] = useReducer(inputReducer, initialState);

  // Action creators for cleaner API
  const actions = {
    setCsvFile: useCallback(
      (file: File | null) => dispatch({ type: "SET_CSV_FILE", payload: file }),
      [],
    ),
    setRulesFile: useCallback(
      (file: File | null) =>
        dispatch({ type: "SET_RULES_FILE", payload: file }),
      [],
    ),
    setRulesText: useCallback(
      (text: string) => dispatch({ type: "SET_RULES_TEXT", payload: text }),
      [],
    ),
    setUseTextRules: useCallback(
      (use: boolean) => dispatch({ type: "SET_USE_TEXT_RULES", payload: use }),
      [],
    ),
    setMetadata: useCallback(
      (text: string) => dispatch({ type: "SET_METADATA", payload: text }),
      [],
    ),
    setMetadataFile: useCallback(
      (file: File | null) =>
        dispatch({ type: "SET_METADATA_FILE", payload: file }),
      [],
    ),
    reset: useCallback(() => dispatch({ type: "RESET" }), []),
  };

  return { state, actions, dispatch };
}
