import React from 'react';
import { ImageQualityReport } from '../../types/api';
import { CheckCircle2, AlertCircle, ShieldAlert } from 'lucide-react';
import { Badge } from '../ui/Badge';

interface QualityReportProps {
  report: ImageQualityReport;
}

export const QualityReport: React.FC<QualityReportProps> = ({ report }) => {
  return (
    <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/60 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          OpenCV Quality Inspection
        </span>
        <Badge variant={report.is_valid ? 'success' : 'danger'} dot>
          {report.is_valid ? 'Quality Passed' : 'Quality Warning'}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="flex items-center justify-between p-2 rounded-lg bg-white/70 border border-slate-100">
          <span className="text-slate-500">Blur Score</span>
          <span className={`font-mono font-semibold ${report.is_blurry ? 'text-rose-600' : 'text-emerald-600'}`}>
            {report.blur_score.toFixed(1)}
          </span>
        </div>
        <div className="flex items-center justify-between p-2 rounded-lg bg-white/70 border border-slate-100">
          <span className="text-slate-500">Brightness Score</span>
          <span className={`font-mono font-semibold ${!report.is_exposure_ok ? 'text-amber-600' : 'text-emerald-600'}`}>
            {report.brightness_score.toFixed(1)}
          </span>
        </div>
      </div>

      {report.warnings && report.warnings.length > 0 && (
        <div className="space-y-1 pt-1">
          {report.warnings.map((w, idx) => (
            <div key={idx} className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 p-2 rounded-lg border border-amber-200/50">
              <AlertCircle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
