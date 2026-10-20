import type { InputHTMLAttributes, Ref } from "react";

type Props = {
  id: string;
  label: string;
  error?: string;
  hint?: string;
  inputRef?: Ref<HTMLInputElement>;
} & Omit<InputHTMLAttributes<HTMLInputElement>, "id">;

/** A labelled input whose hint and error are linked for screen readers (spec 0002, AC-22). */
export function FormField({ id, label, error, hint, inputRef, ...input }: Props) {
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      {hint && (
        <p id={hintId} className="form-hint">
          {hint}
        </p>
      )}
      <input
        id={id}
        ref={inputRef}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        {...input}
      />
      {error && (
        <p id={errorId} className="form-error">
          {error}
        </p>
      )}
    </div>
  );
}
