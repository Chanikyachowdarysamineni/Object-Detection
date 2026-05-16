import { useState, useRef, useCallback } from 'react';
import { Upload, Play, X, Film, AlertCircle } from 'lucide-react';
import { useTheme } from '../lib/theme';
import { useVideoDetection } from '../lib/api.hooks';
import DetectionResults from './DetectionResults';

interface Props {
  confidence: number;
  onModelLoading: (loading: boolean) => void;
}

export default function VideoDetection({ confidence, onModelLoading }: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const { detect, loading, error, result, progress } = useVideoDetection();

  const [videoSrc, setVideoSrc] = useState<string | null>(null);
  const [filename, setFilename] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith('video/')) return;
    setFilename(file.name);
    const url = URL.createObjectURL(file);
    setVideoSrc(url);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const runDetection = async () => {
    if (!videoSrc || !fileInputRef.current?.files?.[0]) return;

    onModelLoading(true);
    try {
      const file = fileInputRef.current.files[0];
      await detect(file, {
        confidence_threshold: confidence,
        frame_skip: 1,
      });
    } finally {
      onModelLoading(false);
    }
  };

  const clearVideo = () => {
    setVideoSrc(null);
    setFilename('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="flex flex-col gap-6">
      {!videoSrc ? (
        <div
          className={`relative border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all duration-200 ${
            isDragging
              ? isDark
                ? 'border-blue-400 bg-blue-950/40'
                : 'border-blue-500 bg-blue-50'
              : isDark
                ? 'border-slate-600 bg-slate-800/40 hover:border-slate-500 hover:bg-slate-800/60'
                : 'border-slate-300 bg-slate-100 hover:border-slate-400 hover:bg-slate-200'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div
            className={`w-16 h-16 rounded-full flex items-center justify-center transition-colors ${
              isDark ? 'bg-slate-700/60' : 'bg-slate-300'
            }`}
          >
            <Upload className={`w-7 h-7 ${isDark ? 'text-slate-300' : 'text-slate-600'}`} />
          </div>
          <div className="text-center">
            <p
              className={`font-medium text-lg ${isDark ? 'text-slate-200' : 'text-slate-900'}`}
            >
              Drop a video here
            </p>
            <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              or click to browse — MP4, WebM, MOV (max 500MB)
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div
            className={`relative rounded-2xl overflow-hidden border ${
              isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-300'
            }`}
          >
            <video
              src={videoSrc}
              controls
              className="w-full max-h-[480px] object-contain"
            />
            <button
              onClick={clearVideo}
              disabled={loading}
              className={`absolute top-3 right-3 w-8 h-8 rounded-full backdrop-blur-sm border flex items-center justify-center transition-colors disabled:opacity-50 ${
                isDark
                  ? 'bg-slate-900/80 border-slate-600 hover:bg-slate-800'
                  : 'bg-white/80 border-slate-300 hover:bg-slate-100'
              }`}
            >
              <X className={`w-4 h-4 ${isDark ? 'text-slate-300' : 'text-slate-600'}`} />
            </button>
          </div>

          {error && (
            <div
              className={`flex items-start gap-3 px-4 py-3 rounded-xl border ${
                isDark
                  ? 'bg-red-950/30 border-red-500/30 text-red-300'
                  : 'bg-red-50 border-red-300 text-red-700'
              }`}
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <p className="text-sm">{error.message}</p>
            </div>
          )}

          {loading && (
            <div
              className={`px-4 py-3 rounded-xl border ${
                isDark
                  ? 'bg-blue-950/30 border-blue-500/30 text-blue-300'
                  : 'bg-blue-50 border-blue-300 text-blue-700'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-4 h-4 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
                <span className="font-medium">Processing video...</span>
              </div>
              <div
                className={`w-full h-2 rounded-full overflow-hidden ${
                  isDark ? 'bg-slate-700' : 'bg-slate-200'
                }`}
              >
                <div
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs mt-1">{Math.round(progress)}%</p>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={runDetection}
              disabled={loading}
              className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-white font-semibold transition-all duration-200 shadow-lg disabled:opacity-60 disabled:cursor-not-allowed ${
                isDark
                  ? 'bg-blue-600 hover:bg-blue-500 shadow-blue-500/20'
                  : 'bg-blue-500 hover:bg-blue-600 shadow-blue-500/30'
              }`}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Process Video
                </>
              )}
            </button>
            <button
              onClick={clearVideo}
              disabled={loading}
              className={`px-4 py-3 rounded-xl border transition-colors disabled:opacity-50 ${
                isDark
                  ? 'border-slate-600 text-slate-300 hover:border-slate-500 hover:text-white'
                  : 'border-slate-400 text-slate-700 hover:border-slate-500 hover:bg-slate-100'
              }`}
            >
              <Film className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {result && result.detected_objects && (
        <DetectionResults
          detections={result.detected_objects}
          stats={{
            total: result.total_objects,
            processingMs: result.processing_ms,
            framesProcessed: result.total_frames,
          }}
        />
      )}
    </div>
  );
}
