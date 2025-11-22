import React from 'react';
import styled from 'styled-components';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  onConfirm: () => void;
  onCancel: () => void;
  type?: 'danger' | 'warning' | 'info';
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title,
  message,
  confirmText,
  cancelText,
  onConfirm,
  onCancel,
  type = 'danger',
}) => {
  if (!isOpen) return null;

  return (
    <Overlay onClick={onCancel}>
      <Modal onClick={(e) => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle>{title}</ModalTitle>
        </ModalHeader>
        
        <ModalBody>
          <ModalMessage>{message}</ModalMessage>
        </ModalBody>
        
        <ModalFooter>
          <CancelButton onClick={onCancel}>
            {cancelText}
          </CancelButton>
          <ConfirmButton $type={type} onClick={onConfirm}>
            {confirmText}
          </ConfirmButton>
        </ModalFooter>
      </Modal>
    </Overlay>
  );
};

export default ConfirmModal;

const Overlay = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease-out;

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`;

const Modal = styled.div`
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 440px;
  width: 90%;
  overflow: hidden;
  animation: slideUp 0.3s ease-out;

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
`;

const ModalHeader = styled.div`
  padding: 24px 24px 16px;
  border-bottom: 1px solid rgba(13, 148, 136, 0.1);
`;

const ModalTitle = styled.h3`
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
`;

const ModalBody = styled.div`
  padding: 24px;
`;

const ModalMessage = styled.p`
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.6;
  color: ${({ theme }) => theme.colors.secondary};
`;

const ModalFooter = styled.div`
  padding: 16px 24px 24px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
`;

const Button = styled.button`
  padding: 10px 24px;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:active {
    transform: scale(0.95);
  }
`;

const CancelButton = styled(Button)`
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme }) => theme.colors.secondary};
  border: 1px solid ${({ theme }) => theme.colors.border};

  &:hover {
    background: rgba(13, 148, 136, 0.05);
    border-color: ${({ theme }) => theme.colors.accent};
    color: ${({ theme }) => theme.colors.primary};
  }
`;

const ConfirmButton = styled(Button)<{ $type: 'danger' | 'warning' | 'info' }>`
  background: ${({ $type }) =>
    $type === 'danger'
      ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
      : $type === 'warning'
      ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
      : 'linear-gradient(135deg, #0d9488 0%, #14b8a6 100%)'};
  color: white;
  box-shadow: ${({ $type }) =>
    $type === 'danger'
      ? '0 4px 12px rgba(239, 68, 68, 0.3)'
      : $type === 'warning'
      ? '0 4px 12px rgba(245, 158, 11, 0.3)'
      : '0 4px 12px rgba(13, 148, 136, 0.3)'};

  &:hover {
    transform: translateY(-2px);
    box-shadow: ${({ $type }) =>
      $type === 'danger'
        ? '0 6px 16px rgba(239, 68, 68, 0.4)'
        : $type === 'warning'
        ? '0 6px 16px rgba(245, 158, 11, 0.4)'
        : '0 6px 16px rgba(13, 148, 136, 0.4)'};
  }
`;
