import React, { useRef } from "react";
import styled from "styled-components";

type ButtonProps = {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  size?: "sm" | "md" | "lg";
  wfull?: boolean; // full width
  disabled?: boolean;
  loading?: boolean;
  ariaLabel?: string;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  className?: string;
};

const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  type = "button",
  size = "md",
  wfull,
  disabled,
  loading,
  ariaLabel,
  iconLeft,
  iconRight,
  className,
}) => {
  const ref = useRef<HTMLButtonElement>(null);

  // shine theo vị trí chuột
  const onMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    const el = e.currentTarget;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--mx", `${e.clientX - rect.left}px`);
    el.style.setProperty("--my", `${e.clientY - rect.top}px`);
  };

  return (
    <Btn
      onMouseMove={onMove}
      onClick={onClick}
      type={type}
      aria-label={ariaLabel}
      disabled={disabled || loading}
      data-size={size}
      data-block={wfull ? "1" : undefined}
      className={className}
      ref={ref}
    >
      {loading ? (
        <span className="spinner" />
      ) : (
        <>
          {iconLeft && <i className="icon left">{iconLeft}</i>}
          <span className="txt">{children}</span>
          {iconRight && <i className="icon right">{iconRight}</i>}
        </>
      )}
    </Btn>
  );
};

export default Button;

const Btn = styled.button`
  --h-sm: 34px;
  --h-md: 42px;
  --h-lg: 48px;

  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;

  height: var(--h-md);
  padding: 0 16px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 800;
  color: #fff;

  /* gradient đồng bộ theo theme */
  background: linear-gradient(
    90deg,
    ${({ theme }) => theme.colors.accent},
    ${({ theme }) => theme.colors.accent2}
  );
  background-size: 140% 100%;
  transition: background-position 0.35s ease, transform 0.15s ease,
    filter 0.15s ease, box-shadow 0.15s ease, opacity 0.2s ease;

  box-shadow: 0 10px 24px rgba(206, 122, 88, 0.25);

  /* shine */
  overflow: hidden;
  &::before {
    content: "";
    position: absolute;
    inset: -1px;
    pointer-events: none;
    background: radial-gradient(
      220px circle at var(--mx, 50%) var(--my, 50%),
      rgba(255, 255, 255, 0.28),
      rgba(255, 255, 255, 0) 40%
    );
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  &:hover {
    background-position: 100% 0;
    filter: brightness(0.98);
  }
  &:hover::before {
    opacity: 1;
  }
  &:active {
    transform: scale(0.98);
  }
  &:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px rgba(206, 122, 88, 0.25),
      0 10px 24px rgba(206, 122, 88, 0.25);
  }
  &[disabled] {
    opacity: 0.6;
    cursor: not-allowed;
    filter: grayscale(0.05);
  }

  /* size */
  &[data-size="sm"] {
    height: var(--h-sm);
    padding: 0 12px;
    border-radius: 10px;
  }
  &[data-size="md"] {
    height: var(--h-md);
  }
  &[data-size="lg"] {
    height: var(--h-lg);
    padding: 0 18px;
    border-radius: 14px;
  }

  /* full width */
  &[data-block="1"] {
    width: 100%;
  }

  .icon {
    display: inline-flex;
  }
  .icon.left {
    margin-left: -2px;
  }
  .icon.right {
    margin-right: -2px;
  }
  .txt {
    line-height: 1;
  }

  /* Spinner animation */
  .spinner {
    width: 20px;
    height: 20px;
    border: 2.5px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`;

