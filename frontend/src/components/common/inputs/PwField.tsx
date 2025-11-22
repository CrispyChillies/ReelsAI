import React, { useState } from "react";
import styled from "styled-components";

type Props = {
  label?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  autoComplete?: string;
  required?: boolean;
  disabled?: boolean;
  name?: string;
  id?: string;
  className?: string; // thêm class nếu cần
};

const PwField: React.FC<Props> = ({
  label,
  value,
  onChange,
  placeholder = "Enter password",
  autoComplete,
  required,
  disabled,
  name,
  id,
  className,
}) => {
  const [show, setShow] = useState(false);

  return (
    <Wrap className={`pwField ${className ?? ""}`}>
      {label && <label htmlFor={id}>{label}</label>}

      <div className="password">
        <input
          id={id}
          name={name}
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required={required}
          disabled={disabled}
        />
        <button
          type="button"
          className="toggle"
          onClick={() => setShow((s) => !s)}
          aria-label={show ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
          title={show ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
          disabled={disabled}
        >
          {show ? eyeOff : eye}
        </button>
      </div>
    </Wrap>
  );
};

export default PwField;

/* ===================== styles ===================== */
const Wrap = styled.div`
  display: block;

  label {
    display: block;
    font-weight: 600;
    font-size: 0.95rem;
    color: ${({ theme }) => theme.colors.primary};
  }

  .password {
    position: relative;
    display: flex;
    align-items: center;
  }

  input {
    height: 38px;
    width: 100%;
    margin-top: 6px;
    padding: 0 48px 0 12px !important;
    border: 1px solid ${({ theme }) => theme.colors.border};
    border-radius: 10px;
    background: #fff;
    color: ${({ theme }) => theme.colors.primary};
    font-size: 1rem;
    outline: none;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }
  input::placeholder {
    color: ${({ theme }) => theme.colors.secondary};
    opacity: 0.8;
  }
  input:focus {
    border-color: ${({ theme }) => theme.colors.accent};
    box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.2);
  }
  input:disabled {
    background: ${({ theme }) => theme.colors.surface2};
    color: ${({ theme }) => theme.colors.secondary};
    cursor: not-allowed;
  }

  .toggle {
    position: absolute;
    right: 6px;
    top: calc(50% + 3px);
    transform: translateY(-50%);
    width: 36px;
    height: 36px;
    border: none;
    background: transparent;
    cursor: pointer;
    color: ${({ theme }) => theme.colors.secondary};
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .toggle:hover {
    color: ${({ theme }) => theme.colors.accent};
    background: rgba(13, 148, 136, 0.1);
  }
  .toggle:focus-visible {
    outline: 3px solid rgba(13, 148, 136, 0.35);
    outline-offset: 2px;
  }
  .toggle svg {
    width: 18px;
    height: 18px;
    display: block;
  }
`;

/* Icons */
const eye = (
  <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
    <path
      d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    />
    <circle
      cx="12"
      cy="12"
      r="3"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);
const eyeOff = (
  <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
    <path
      d="M3 3l18 18"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
    <path
      d="M1 12s4-7 11-7c2.2 0 4.1.6 5.7 1.5M22 12s-4 7-11 7c-2.2 0-4.1-.6-5.7-1.5"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);
