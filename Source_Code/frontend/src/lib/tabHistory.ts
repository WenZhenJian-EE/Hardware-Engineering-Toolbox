import { useState, useEffect } from 'react';

export function useTabHistoryState<T>(
  initialValue: T | (() => T),
  stateKey: string
) {
  const [state, setState] = useState<T>(initialValue);

  const setTrackedState = (newValue: T | ((prev: T) => T)) => {
    setState((prev) => {
      const resolved = typeof newValue === 'function' ? (newValue as Function)(prev) : newValue;
      if (resolved !== prev) {
        queueMicrotask(() => {
          window.dispatchEvent(new CustomEvent('app-state-push', {
            detail: {
              stateKey,
              value: resolved,
              prevValue: prev,
              restore: setState
            }
          }));
        });
      }
      return resolved;
    });
  };

  return [state, setTrackedState] as const;
}
