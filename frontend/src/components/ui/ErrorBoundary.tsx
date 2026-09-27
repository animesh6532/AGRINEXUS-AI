import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { Button } from './Button';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an unhandled rendering error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 sm:p-8 flex items-center justify-center min-h-[400px]">
          <GlassCard variant="cream" className="max-w-xl w-full p-6 sm:p-8 space-y-6 text-center shadow-xl border-amber-200">
            <div className="w-14 h-14 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center mx-auto shadow-sm">
              <AlertTriangle className="w-8 h-8 text-amber-700" />
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-widest text-[#536056] block">
                SYSTEM RECOVERY SHIELD
              </span>
              <h2 className="text-2xl font-black font-editorial text-[#0B1C10]">
                {this.props.fallbackTitle || 'Crop Module Encountered an Issue'}
              </h2>
              <p className="text-xs sm:text-sm text-[#536056] leading-relaxed max-w-md mx-auto">
                {this.props.fallbackMessage ||
                  'An unexpected rendering error occurred while loading this view. The rest of AGRINEXUS remains active.'}
              </p>
            </div>

            {this.state.error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-left text-xs font-mono break-all max-h-32 overflow-y-auto">
                {this.state.error.message || String(this.state.error)}
              </div>
            )}

            <div className="flex items-center justify-center gap-3 flex-wrap pt-2">
              <Button
                variant="lime"
                size="md"
                onClick={this.handleReset}
                icon={<RefreshCw className="w-4 h-4" />}
              >
                Try Again
              </Button>
              <Button
                variant="secondary"
                size="md"
                onClick={() => { window.location.href = '/dashboard'; }}
                icon={<Home className="w-4 h-4" />}
              >
                Back to Dashboard
              </Button>
            </div>
          </GlassCard>
        </div>
      );
    }

    return this.props.children;
  }
}
