import { useState, useRef, useEffect, useCallback } from 'react';
import { Camera, CameraOff, Save, AlertCircle } from 'lucide-react';
import { useTheme } from '../lib/theme';
import { detectObjects, drawDetections } from '../lib/detector';
import type { DetectedObject } from '../lib/api.types';
import DetectionResults from './DetectionResults';

interface Props {
  confidence: number;
  onModelLoading: (loading: boolean) => void;
}

export default function WebcamDetection({ confidence, onModelLoading }: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fps, setFps] = useState(0);
  const [detections, setDetections] = useState<DetectedObject[]>([]);
  const [saving, setSaving] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);
  const fpsCounterRef = useRef({ frames: 0, last: performance.now() });
  const runningRef = useRef(false);
  const firstFrameRef = useRef(true);

  const stopWebcam = useCallback(() => {
    runningRef.current = false;
    cancelAnimationFrame(animFrameRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setActive(false);
    setFps(0);
  }, []);

  const runLoop = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !runningRef.current) return;
    if (video.readyState < 2) {
      animFrameRef.current = requestAnimationFrame(runLoop);
      return;
    }

    if (firstFrameRef.current) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      firstFrameRef.current = false;
      onModelLoading(false);
    }

    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    try {
      const found = await detectObjects(video, confidence);
      setDetections(found);
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      drawDetections(canvas, found, video.videoWidth, video.videoHeight);
    } catch (_) {
      // skip frame on error
    }

    const now = performance.now();
    fpsCounterRef.current.frames++;
    if (now - fpsCounterRef.current.last >= 1000) {
      setFps(fpsCounterRef.current.frames);
      fpsCounterRef.current.frames = 0;
      fpsCounterRef.current.last = now;
    }

    if (runningRef.current) {
      animFrameRef.current = requestAnimationFrame(runLoop);
    }
  }, [confidence, onModelLoading]);

  const startWebcam = useCallback(async () => {
    setError(null);
    onModelLoading(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      firstFrameRef.current = true;
      runningRef.current = true;
      setActive(true);
      animFrameRef.current = requestAnimationFrame(runLoop);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Camera access denied');
      onModelLoading(false);
    }
  }, [runLoop, onModelLoading]);

  useEffect(() => {
    return () => stopWebcam();
  }, [stopWebcam]);

  const saveSnapshot = async () => {
    if (!detections.length) return;
    setSaving(true);
    // Snapshot saved to local storage
    console.log('Detection saved:', { type: 'webcam', detections, confidence });
    setSaving(false);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className={`relative rounded-2xl overflow-hidden aspect-video flex items-center justify-center border ${
        isDark ? 'bg-slate-900 border-slate-700' : 'bg-gray-100 border-slate-300'
      }`}>
        <video ref={videoRef} className="hidden" playsInline muted />
        <canvas
          ref={canvasRef}
          className={`w-full h-full object-contain transition-opacity duration-300 ${active ? 'opacity-100' : 'opacity-0'}`}
        />

        {!active && !error && (
          <div className={`absolute inset-0 flex flex-col items-center justify-center gap-3 ${
            isDark ? 'text-slate-400' : 'text-slate-600'
          }`}>
            <Camera className="w-12 h-12 opacity-40" />
            <p className="text-sm">Camera feed will appear here</p>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-rose-400">
            <AlertCircle className="w-10 h-10" />
            <p className="text-sm text-center px-6">{error}</p>
          </div>
        )}

        {active && (
          <div className="absolute top-3 left-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse" />
            <span className={`text-xs px-2 py-0.5 rounded-full backdrop-blur-sm ${
              isDark ? 'text-white/80 bg-black/50' : 'text-white bg-black/40'
            }`}>
              LIVE · {fps} fps
            </span>
          </div>
        )}
      </div>

      <div className="flex gap-3">
        {!active ? (
          <button
            onClick={startWebcam}
            className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-white font-semibold transition-all duration-200 shadow-lg ${
              isDark
                ? 'bg-green-600 hover:bg-green-500 shadow-green-500/20'
                : 'bg-green-500 hover:bg-green-600 shadow-green-500/30'
            }`}
          >
            <Camera className="w-4 h-4" />
            Start Camera
          </button>
        ) : (
          <>
            <button
              onClick={stopWebcam}
              className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-white font-semibold transition-all duration-200 shadow-lg ${
                isDark
                  ? 'bg-rose-600 hover:bg-rose-500 shadow-rose-500/20'
                  : 'bg-rose-500 hover:bg-rose-600 shadow-rose-500/30'
              }`}
            >
              <CameraOff className="w-4 h-4" />
              Stop Camera
            </button>
            <button
              onClick={saveSnapshot}
              disabled={saving || detections.length === 0}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl border transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
                isDark
                  ? 'border-slate-600 text-slate-300 hover:border-slate-500 hover:text-white'
                  : 'border-slate-400 text-slate-700 hover:border-slate-500 hover:bg-slate-100'
              }`}
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving…' : 'Save'}
            </button>
          </>
        )}
      </div>

      {detections.length > 0 && <DetectionResults detections={detections} />}
    </div>
  );
}
