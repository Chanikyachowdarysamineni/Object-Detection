import { Cpu, Layers, Info, AlertCircle, RefreshCw } from 'lucide-react';
import { useTheme } from '../lib/theme';
import { useModelInfo } from '../lib/api.hooks';

export default function ModelInfo() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const { data: modelInfo, loading, error } = useModelInfo();

  if (loading) {
    return (
      <div className="flex flex-col gap-6">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-32 rounded-2xl animate-pulse ${isDark ? 'bg-slate-800/60' : 'bg-slate-300/60'}`}
          />
        ))}
      </div>
    );
  }

  if (error || !modelInfo) {
    return (
      <div
        className={`flex items-start gap-3 px-4 py-3 rounded-xl border ${
          isDark
            ? 'bg-red-950/30 border-red-500/30 text-red-300'
            : 'bg-red-50 border-red-300 text-red-700'
        }`}
      >
        <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <p className="text-sm">Failed to load model information: {error?.message}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Model Architecture */}
      <div
        className={`rounded-2xl border overflow-hidden transition-colors ${
          isDark ? 'border-slate-700 bg-slate-800/50' : 'border-slate-300 bg-slate-100/50'
        }`}
      >
        <div
          className={`px-5 py-4 border-b flex items-center gap-2 ${isDark ? 'border-slate-700/60' : 'border-slate-300'}`}
        >
          <Cpu className={`w-4 h-4 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
            Model Architecture
          </h3>
        </div>
        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1">
            <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
              Name
            </span>
            <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
              {modelInfo.model_name}
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
              Framework
            </span>
            <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
              PyTorch + Ultralytics
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
              Device
            </span>
            <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
              {modelInfo.device}
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
              Classes
            </span>
            <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
              {modelInfo.num_classes} categories
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
              Version
            </span>
            <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
              YOLOv8 Nano
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className={`text-xs uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
              Input Size
            </span>
            <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
              640x640
            </span>
          </div>
        </div>
      </div>

      {/* Detectable Classes */}
      <div
        className={`rounded-2xl border overflow-hidden transition-colors ${
          isDark ? 'border-slate-700 bg-slate-800/50' : 'border-slate-300 bg-slate-100/50'
        }`}
      >
        <div
          className={`px-5 py-4 border-b flex items-center gap-2 ${isDark ? 'border-slate-700/60' : 'border-slate-300'}`}
        >
          <Layers className={`w-4 h-4 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
            Detectable Classes ({modelInfo.num_classes})
          </h3>
        </div>
        <div
          className={`p-5 flex flex-wrap gap-1.5 max-h-80 overflow-y-auto ${isDark ? 'bg-slate-900/20' : 'bg-slate-200/20'}`}
        >
          {modelInfo.class_names && modelInfo.class_names.length > 0 ? (
            modelInfo.class_names.map((cls, idx) => (
              <span
                key={idx}
                className={`text-xs px-2.5 py-1 rounded-full capitalize transition-colors ${
                  isDark ? 'bg-slate-700/60 text-slate-300' : 'bg-slate-300 text-slate-700'
                }`}
              >
                {cls}
              </span>
            ))
          ) : (
            <span className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              Class names not available
            </span>
          )}
        </div>
      </div>

      {/* Info */}
      <div
        className={`rounded-2xl border p-5 flex items-start gap-3 transition-colors ${
          isDark ? 'border-slate-700/60 bg-slate-800/30' : 'border-slate-300 bg-slate-100/30'
        }`}
      >
        <Info className={`w-4 h-4 flex-shrink-0 mt-0.5 ${isDark ? 'text-slate-500' : 'text-slate-600'}`} />
        <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-700'}`}>
          <span className={isDark ? 'text-slate-300' : 'text-slate-900'}>
            {modelInfo.model_name}
          </span>{' '}
          is a state-of-the-art object detection model running on your backend server. It processes images and videos
          with high accuracy. All detection results are returned to your browser for display.
        </p>
      </div>
    </div>
  );
}
