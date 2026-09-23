import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, VideoOff, Play, Pause, RefreshCw, Activity, ShieldCheck, AlertTriangle } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { QualityReport } from '../components/intelligence/QualityReport';
import { api } from '../services/api';
import { FramePredictionResponse } from '../types/api';

export const LiveCameraPage: React.FC = () => {
  const [mode, setMode] = useState<'disease' | 'pest'>('disease');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [fps, setFps] = useState<number>(2); // 2 frames per second sampling
  const [lastPrediction, setLastPrediction] = useState<FramePredictionResponse | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<any>(null);

  // Start Browser Camera
  const startCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' },
        audio: false
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsStreaming(true);
      setIsPaused(false);
    } catch (err: any) {
      setCameraError('Camera access denied or device not found: ' + err.message);
      setIsStreaming(false);
    }
  };

  // Stop Browser Camera
  const stopCamera = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
    setIsPaused(false);
  }, []);

  // Frame Capture and REST Inference Loop
  const captureAndSendFrame = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || isPaused) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video.readyState < 2) return;

    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      if (!blob) return;
      try {
        let res: FramePredictionResponse;
        if (mode === 'disease') {
          res = await api.processDiseaseLiveFrame(blob);
        } else {
          res = await api.processPestLiveFrame(blob);
        }
        setLastPrediction(res);
      } catch {
        // Suppress individual frame drop errors
      }
    }, 'image/jpeg', 0.85);
  }, [isPaused, mode]);

  useEffect(() => {
    if (isStreaming && !isPaused) {
      const intervalMs = 1000 / fps;
      intervalRef.current = setInterval(captureAndSendFrame, intervalMs);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isStreaming, isPaused, fps, captureAndSendFrame]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center font-bold">
            <Camera className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Live Camera Computer Vision</h1>
            <p className="text-xs text-slate-500">
              OpenCV real-time frame inspection, PyTorch model evaluation, and session temporal prediction smoothing.
            </p>
          </div>
        </div>

        {/* Mode Switcher Buttons */}
        <div className="flex items-center gap-2 p-1 rounded-xl bg-white/70 border border-slate-200">
          <button
            onClick={() => setMode('disease')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              mode === 'disease' ? 'bg-primary-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Plant Disease Mode
          </button>
          <button
            onClick={() => setMode('pest')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              mode === 'pest' ? 'bg-amber-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Visual Pest Mode
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Camera Viewport Column */}
        <GlassCard variant="strong" className="p-4 lg:col-span-2 space-y-4">
          <div className="relative aspect-video rounded-2xl bg-slate-950 overflow-hidden flex items-center justify-center border border-slate-800">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover ${isStreaming ? 'block' : 'hidden'}`}
            />

            {!isStreaming && (
              <div className="text-center space-y-3 p-6 text-slate-400">
                <Camera className="w-12 h-12 mx-auto text-slate-600" />
                <p className="text-xs font-medium">Click "Start Live Camera Feed" to initialize WebRTC browser stream.</p>
              </div>
            )}

            {/* Hidden Canvas element used for frame capture */}
            <canvas ref={canvasRef} className="hidden" />

            {/* HUD Overlay when streaming */}
            {isStreaming && (
              <>
                <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-xl text-[10px] text-white flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-rose-500 animate-pulse" />
                  <span>{mode === 'disease' ? 'ResNet18 Disease Feed' : 'MobileNetV3 Pest Feed'} ({fps} FPS)</span>
                </div>

                {lastPrediction && (
                  <div className="absolute bottom-3 left-3 right-3 bg-slate-900/90 backdrop-blur-md p-4 rounded-xl text-white flex items-center justify-between border border-slate-700">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Smoothed Live Prediction</span>
                      <p className="text-base font-black text-white capitalize">{lastPrediction.prediction.replace(/___/g, ' - ').replace(/_/g, ' ')}</p>
                      <p className="text-[10px] text-slate-400">Raw: {lastPrediction.raw_prediction}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant={lastPrediction.confidence > 0.5 ? 'success' : 'warning'}>
                        {(lastPrediction.confidence * 100).toFixed(1)}% Conf
                      </Badge>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Control Buttons Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-2">
              {!isStreaming ? (
                <Button variant="primary" size="md" onClick={startCamera} icon={<Play className="w-4 h-4" />}>
                  Start Live Camera Feed
                </Button>
              ) : (
                <>
                  <Button variant="danger" size="md" onClick={stopCamera} icon={<VideoOff className="w-4 h-4" />}>
                    Stop Camera
                  </Button>
                  <Button
                    variant="outline"
                    size="md"
                    onClick={() => setIsPaused(!isPaused)}
                    icon={isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                  >
                    {isPaused ? 'Resume Feed' : 'Pause Stream'}
                  </Button>
                </>
              )}
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-600">
              <span>Sampling Rate:</span>
              <select
                value={fps}
                onChange={(e) => setFps(parseInt(e.target.value))}
                className="glass-input rounded-lg px-2 py-1 text-xs"
              >
                <option value={1}>1 FPS</option>
                <option value={2}>2 FPS (Recommended)</option>
                <option value={5}>5 FPS</option>
              </select>
            </div>
          </div>
        </GlassCard>

        {/* Live OpenCV Inspection Side Panel */}
        <div className="space-y-6">
          {cameraError && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{cameraError}</span>
            </div>
          )}

          {lastPrediction ? (
            <GlassCard variant="strong" className="p-6 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Live Frame Inspection</h3>
              <QualityReport report={lastPrediction.quality_report} />
            </GlassCard>
          ) : (
            <GlassCard className="p-8 text-center space-y-3">
              <ShieldCheck className="w-8 h-8 text-slate-300 mx-auto" />
              <h3 className="text-sm font-bold text-slate-700">OpenCV Quality Inspection Ready</h3>
              <p className="text-xs text-slate-500">
                Frame Laplacian blur scores and mean exposure brightness metrics will appear here live during streaming.
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
};
