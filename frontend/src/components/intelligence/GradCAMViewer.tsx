import React, { useState } from 'react';
import { Eye, EyeOff, Layers } from 'lucide-react';
import { Button } from '../ui/Button';

interface GradCAMViewerProps {
  heatmapBase64: string | null;
  available: boolean;
}

export const GradCAMViewer: React.FC<GradCAMViewerProps> = ({ heatmapBase64, available }) => {
  const [showHeatmap, setShowHeatmap] = useState<boolean>(true);

  if (!available || !heatmapBase64) {
    return (
      <div className="p-3 text-xs text-slate-400 bg-slate-50/50 rounded-xl border border-slate-200/40 italic">
        Grad-CAM visual explanation overlay not generated for this image.
      </div>
    );
  }

  const imageSrc = heatmapBase64.startsWith('data:image')
    ? heatmapBase64
    : `data:image/png;base64,${heatmapBase64}`;

  return (
    <div className="space-y-3 p-4 rounded-xl bg-white/80 border border-slate-200/80 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-primary-600" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">
            Grad-CAM Visual Attention Map
          </span>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowHeatmap(!showHeatmap)}
          icon={showHeatmap ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
        >
          {showHeatmap ? 'Hide Overlay' : 'Show Overlay'}
        </Button>
      </div>

      {showHeatmap && (
        <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-900 group">
          <img
            src={imageSrc}
            alt="Grad-CAM Visual Heatmap"
            className="w-full h-auto max-h-72 object-contain mx-auto transition-transform duration-300 group-hover:scale-105"
          />
          <div className="absolute bottom-2 left-2 right-2 p-2 bg-slate-900/80 backdrop-blur-md rounded-lg text-[10px] text-slate-200 text-center">
            Highlighted warm regions indicate features influencing the ResNet18 model decision.
          </div>
        </div>
      )}
    </div>
  );
};
