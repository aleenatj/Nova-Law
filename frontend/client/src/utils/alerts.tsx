import React from "react";

export type AlertType = 'success' | 'error' | 'warning' | 'info';

export interface AlertMessage {
  id: string;
  type: AlertType;
  title: string;
  message: string;
  duration?: number;
  dismissible?: boolean;
}

export interface AlertProps {
  alert: AlertMessage;
  onDismiss: (id: string) => void;
}

// Simple Alert component
export function Alert({ alert, onDismiss }: AlertProps) {
  const getAlertStyles = (type: AlertType) => {
    switch (type) {
      case 'success': return 'bg-green-200 border-green-200 text-green-800';
      case 'error': return 'bg-red-200 border-red-200 text-red-800';
      case 'warning': return 'bg-yellow-200 border-yellow-200 text-yellow-800';
      case 'info': return 'bg-blue-200 border-blue-200 text-blue-800';
      default: return 'bg-gray-200 border-gray-200 text-gray-800';
    }
  };

  const getIcon = (type: AlertType) => {
    switch (type) {
      case 'success': return '✓';
      case 'error': return '✕';
      case 'warning': return '⚠';
      case 'info': return 'ℹ';
      default: return '•';
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getAlertStyles(alert.type)}`}>
      <div className="flex items-start gap-3">
        <span className="text-lg">{getIcon(alert.type)}</span>
        <div className="flex-1">
          <h3 className="font-medium">{alert.title}</h3>
          <p className="text-sm mt-1">{alert.message}</p>
        </div>
        {alert.dismissible && (
          <button
            onClick={() => onDismiss(alert.id)}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}

// Alert container
export function AlertContainer({ alerts, onDismiss }: { alerts: AlertMessage[]; onDismiss: (id: string) => void }) {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {alerts.map((alert) => (
        <Alert key={alert.id} alert={alert} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

// Simple alert creators
export function createAlert(type: AlertType, title: string, message: string, duration = 5000): AlertMessage {
  return {
    id: Date.now().toString(),
    type,
    title,
    message,
    duration,
    dismissible: true
  };
}

export function createSuccessAlert(title: string, message: string, duration?: number) {
  return createAlert('success', title, message, duration);
}

export function createErrorAlert(title: string, message: string, duration?: number) {
  return createAlert('error', title, message, duration);
}

export function createWarningAlert(title: string, message: string, duration?: number) {
  return createAlert('warning', title, message, duration);
}

export function createInfoAlert(title: string, message: string, duration?: number) {
  return createAlert('info', title, message, duration);
}


