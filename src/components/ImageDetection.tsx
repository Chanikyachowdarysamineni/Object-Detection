import { useState, useRef, useCallback } from 'react';
import { Upload, Scan, X, Image as ImageIcon, AlertCircle } from 'lucide-react';
import { useTheme } from '../lib/theme';
import { useImageDetection } from '../lib/api.hooks';
import type { DetectedObject } from '../lib/api.types';
import DetectionResults from './DetectionResults';

interface Props {
  confidence: number;
  onModelLoading: (loading: boolean) => void;
}

export default function ImageDetection({ confidence, onModelLoading }: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const { detect, loading, error, result } = useImageDetection();
  
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);
  const imgRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return;
    setFilename(file.name);
    const url = URL.createObjectURL(file);
    setImageSrc(url);
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
    if (!imageSrc || !imgRef.current?.files?.[0]) return;
    
    onModelLoading(true);
    try {
      const file = imgRef.current.files[0];
      await detect(file, {
        confidence_threshold: confidence,
      });
    } finally {
      onModelLoading(false);
    }
  };

  const clearImage = () => {
    setImageSrc(null);
    setFilename('');
    if (imgRef.current) imgRef.current.value = '';
  };

  return (
    <div className="flex flex-col gap-6">
      {!imageSrc ? (
        <div
          className={`relative border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all duration-200 ${
            isDragging
              ? isDark
                ? 'border-green-400 bg-green-950/40'
                : 'border-green-500 bg-green-50'
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
          onClick={() => imgRef.current?.click()}
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
              Drop an image here
            </p>
            <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              or click to browse — PNG, JPG, WEBP
            </p>
          </div>
          <input
            ref={imgRef}
            type="file"
            accept="image/*"
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
            <img
              src={imageSrc}
              alt="Uploaded"
              className="w-full object-contain max-h-[480px]"
              crossOrigin="anonymous"
            />
            <button
              onClick={clearImage}
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

          <div className="flex gap-3">
            <button
              onClick={runDetection}
              disabled={loading}
              className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-white font-semibold transition-all duration-200 shadow-lg disabled:opacity-60 disabled:cursor-not-allowed ${
                isDark
                  ? 'bg-green-600 hover:bg-green-500 shadow-green-500/20'
                  : 'bg-green-500 hover:bg-green-600 shadow-green-500/30'
              }`}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Detecting…
                </>
              ) : (
                <>
                  <Scan className="w-4 h-4" />
                  Detect Objects
                </>
              )}
            </button>
            <button
              onClick={clearImage}
              disabled={loading}
              className={`px-4 py-3 rounded-xl border transition-colors disabled:opacity-50 ${
                isDark
                  ? 'border-slate-600 text-slate-300 hover:border-slate-500 hover:text-white'
                  : 'border-slate-400 text-slate-700 hover:border-slate-500 hover:bg-slate-100'
              }`}
            >
              <ImageIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {result && result.detected_objects && (
        <DetectionResults detections={result.detected_objects} stats={{
          total: result.total_objects,
          processingMs: result.processing_ms
        }} />
      )}
    </div>
  );
}
