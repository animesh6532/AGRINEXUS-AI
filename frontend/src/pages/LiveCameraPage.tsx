import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, VideoOff, Play, Pause, Activity, ShieldCheck, AlertTriangle, RefreshCw, Eye } from 'lucide-react';
import { AgriculturalPageHero } from '../components/design/AgriculturalPageHero';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { QualityReport } from '../components/intelligence/QualityReport';
import { ScopeWarning } from '../components/intelligence/ScopeWarning';
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
    <div className="space-y-8 selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* Page Hero */}
      <AgriculturalPageHero
        category="LIVE VISION"
        title="AI Field Vision Studio"
        description="Real-time video frame inference with OpenCV image quality inspection gates, temporal prediction smoothing, and instant disease/pest detection."
        imageSrc="/images/smart-farming.webp"
      />

      {/* Mode Selector & Control Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] border border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-widest text-[#D4E768] mr-2">
            DETECTION MODE:
          </span>
          <button
            onClick={() => setMode('disease')}
            className={`px-4 py-2 rounded-full text-xs font-extrabold transition-all ${
              mode === 'disease'
                ? 'bg-[#D4E768] text-[#0B1C10] shadow-sm'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            Plant Disease Diagnosis (ResNet18)
          </button>
          <button
            onClick={() => setMode('pest')}
            className={`px-4 py-2 rounded-full text-xs font-extrabold transition-all ${
              mode === 'pest'
                ? 'bg-[#D4E768] text-[#0B1C10] shadow-sm'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            Visual Insect Species (MobileNetV3)
          </button>
        </div>

        <div className="flex items-center gap-3 text-xs text-white/80">
          <span className="font-semibold">Sampling Rate:</span>
          <select
            value={fps}
            onChange={(e) => setFps(parseInt(e.target.value))}
            className="bg-[#112316] text-[#D4E768] border border-white/20 rounded-full px-3 py-1.5 text-xs font-mono font-bold focus:outline-none"
          >
            <option value={1}>1 FPS</option>
            <option value={2}>2 FPS (Recommended)</option>
            <option value={5}>5 FPS</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main 16:9 Camera Viewport (8 Cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="relative aspect-video rounded-3xl bg-[#07120A] overflow-hidden flex items-center justify-center border-2 border-[#E2E7DA]/20 shadow-2xl group">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover ${isStreaming ? 'block' : 'hidden'}`}
            />

            {!isStreaming && (
              <div className="text-center space-y-4 p-8 text-white/60 relative z-10 max-w-md">
                <div className="w-16 h-16 rounded-3xl bg-white/10 backdrop-blur-md flex items-center justify-center mx-auto text-[#D4E768]">
                  <Camera className="w-8 h-8" />
                </div>
                <div>
                  <h3 className="text-lg font-extrabold font-editorial text-white">Live Camera Vision Offline</h3>
                  <p className="text-xs text-white/60 mt-1">
                    Initialize your device camera feed to begin streaming live frames to OpenCV quality gates and PyTorch models.
                  </p>
                </div>
                <Button variant="lime" size="md" onClick={startCamera} icon={<Play className="w-4 h-4" />}>
                  Start Live Camera Feed
                </Button>
              </div>
            )}

            {/* Hidden Canvas for frame capture */}
            <canvas ref={canvasRef} className="hidden" />

            {/* HUD Overlay when streaming */}
            {isStreaming && (
              <>
                <div className="absolute top-4 left-4 bg-[#0B1C10]/85 backdrop-blur-md px-3.5 py-1.5 rounded-full text-xs text-white flex items-center gap-2 border border-white/15">
                  <Activity className="w-3.5 h-3.5 text-[#D4E768] animate-pulse" />
                  <span className="font-bold">
                    LIVE {mode.toUpperCase()} STREAM • {fps} FPS
                  </span>
                </div>

                {lastPrediction && (
                  <div className="absolute bottom-4 left-4 right-4 bg-[#0B1C10]/90 backdrop-blur-xl p-5 rounded-2xl text-white flex items-center justify-between border border-[#D4E768]/30 shadow-floating">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-[#D4E768] tracking-widest block">
                        Smoothed Temporal Prediction
                      </span>
                      <p className="text-lg font-black font-editorial text-white capitalize mt-0.5">
                        {lastPrediction.prediction.replace(/___/g, ' — ').replace(/_/g, ' ')}
                      </p>
                      <p className="text-[10px] text-white/50 font-mono">Raw: {lastPrediction.raw_prediction}</p>
                    </div>

                    <div className="text-right">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-[#D4E768] text-[#0B1C10]">
                        {(lastPrediction.confidence * 100).toFixed(1)}% Confidence
                      </span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Controls Bar */}
          {isStreaming && (
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-white border border-[#E2E7DA]">
              <div className="flex items-center gap-3">
                <Button variant="danger" size="md" onClick={stopCamera} icon={<VideoOff className="w-4 h-4" />}>
                  Stop Camera Stream
                </Button>
                <Button
                  variant="outline"
                  size="md"
                  onClick={() => setIsPaused(!isPaused)}
                  icon={isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                >
                  {isPaused ? 'Resume Inference' : 'Pause Frame Capture'}
                </Button>
              </div>

              <span className="text-xs text-[#536056] font-semibold">
                Status: {isPaused ? 'Paused' : 'Active Streaming'}
              </span>
            </div>
          )}
        </div>

        {/* Live OpenCV Inspection Side Panel (4 Cols) */}
        <div className="lg:col-span-4 space-y-6">
          {cameraError && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{cameraError}</span>
            </div>
          )}

          {lastPrediction ? (
            <GlassCard variant="solid" className="p-6 space-y-5">
              <div className="border-b border-[#E2E7DA] pb-3">
                <span className="text-xs font-bold uppercase tracking-widest text-[#536056] block">
                  OPENCV FRAME QUALITY
                </span>
                <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                  Live Frame Quality Inspection
                </h3>
              </div>

              <QualityReport report={lastPrediction.quality_report} />
            </GlassCard>
          ) : (
            <GlassCard variant="cream" className="p-8 text-center space-y-3">
              <ShieldCheck className="w-10 h-10 text-[#2F6B3C] mx-auto" />
              <h3 className="text-base font-extrabold font-editorial text-[#0B1C10]">
                OpenCV Quality Engine Ready
              </h3>
              <p className="text-xs text-[#536056] leading-relaxed">
                Laplacian variance blur scores, brightness metrics, and frame exposure quality warnings will display here in real time once camera feed begins.
              </p>
            </GlassCard>
          )}

          <ScopeWarning
            type="info"
            message="Live vision captures video frames via WebRTC and evaluates them through FastAPI REST frame inference endpoints using session temporal smoothing."
          />
        </div>
      </div>
    </div>
  );
};
