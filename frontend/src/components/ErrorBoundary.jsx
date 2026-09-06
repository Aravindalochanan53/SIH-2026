import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-app, #F8FAFC)',
          padding: '20px',
        }}>
          <div style={{
            background: 'var(--bg-surface, #FFFFFF)',
            border: '1px solid var(--border-color, #E2E8F0)',
            borderRadius: '16px',
            padding: '36px',
            maxWidth: '480px',
            textAlign: 'center',
            boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
          }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '12px',
              background: 'rgba(239, 68, 68, 0.1)',
              color: '#EF4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
            }}>
              <AlertTriangle size={26} />
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary, #0F172A)', margin: '0 0 8px' }}>
              Something went wrong
            </h2>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary, #475569)', margin: '0 0 20px', lineHeight: 1.5 }}>
              {this.state.error?.message || 'An unexpected rendering error occurred.'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                background: 'linear-gradient(135deg, #2563EB 0%, #06B6D4 100%)',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '14px',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={16} />
              <span>Reload Application</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
