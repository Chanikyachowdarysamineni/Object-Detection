import { useState } from 'react';
import { ScanSearch, Camera, Film, Image as ImageIcon, History, Info, Sliders, Sun, Moon } from 'lucide-react';
import { useTheme } from './lib/theme';
import ImageDetection from './components/ImageDetection';
import WebcamDetection from './components/WebcamDetection';
import VideoDetection from './components/VideoDetection';
import DetectionLog from './components/DetectionLog';
import ModelInfo from './components/ModelInfo';

type Tab = 'image' | 'webcam' | 'video' | 'log' | 'model';

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'image', label: 'Image', icon: <ImageIcon className="w-4 h-4" /> },
  { id: 'webcam', label: 'Webcam', icon: <Camera className="w-4 h-4" /> },
  { id: 'video', label: 'Video', icon: <Film className="w-4 h-4" /> },
  { id: 'log', label: 'Log', icon: <History className="w-4 h-4" /> },
  { id: 'model', label: 'Model', icon: <Info className="w-4 h-4" /> },
];

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [tab, setTab] = useState<Tab>('image');
  const [confidence, setConfidence] = useState(0.5);
  const [modelLoading, setModelLoading] = useState(false);

  const isDark = theme === 'dark';

  return (
    <div className={`min-h-screen font-sans transition-colors duration-200 ${
      isDark 
        ? 'bg-slate-950 text-white' 
        : 'bg-white text-slate-900'
    }`}>
      <div className="fixed inset-0 pointer-events-none">
        {isDark ? (
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(14,165,233,0.08),transparent)]" />
        ) : (
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.08),transparent)]" />
        )}
      </div>

      <div className="relative z-10 max-w-4xl mx-auto px-4 py-8">
        <header className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
              isDark
                ? 'bg-blue-500/15 border border-blue-500/30'
                : 'bg-blue-100 border border-blue-300'
            }`}>
              <ScanSearch className={`w-5 h-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
            </div>
            <div className="flex-1">
              <h1 className={`text-2xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Object Detection
              </h1>
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                Powered by COCO-SSD · TensorFlow.js
              </p>
            </div>
            <button
              onClick={toggleTheme}
              className={`p-2.5 rounded-xl border transition-all duration-200 ${
                isDark
                  ? 'bg-slate-800 border-slate-700 hover:bg-slate-700 text-yellow-400'
                  : 'bg-slate-100 border-slate-300 hover:bg-slate-200 text-blue-600'
              }`}
              title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            {modelLoading && (
              <div className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition-colors ${
                isDark
                  ? 'text-blue-400 bg-blue-500/10 border-blue-500/20'
                  : 'text-blue-600 bg-blue-100 border-blue-300'
              }`}>
                <span className="w-3 h-3 border-2 rounded-full animate-spin" style={{
                  borderColor: isDark ? 'rgba(96, 165, 250, 0.3)' : 'rgba(59, 130, 246, 0.3)',
                  borderTopColor: isDark ? 'rgb(96, 165, 250)' : 'rgb(59, 130, 246)'
                }} />
                Loading model…
              </div>
            )}
          </div>
        </header>

        {(tab === 'image' || tab === 'webcam' || tab === 'video') && (
          <div className={`mb-6 flex items-center gap-4 rounded-2xl px-5 py-4 border transition-colors ${
            isDark
              ? 'bg-slate-800/50 border-slate-700/60'
              : 'bg-slate-100/50 border-slate-300'
          }`}>
            <div className="flex items-center gap-2 flex-shrink-0">
              <Sliders className={`w-4 h-4 ${isDark ? 'text-slate-400' : 'text-slate-600'}`} />
              <span className={`text-sm font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Confidence
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="0.95"
              step="0.05"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className={`flex-1 h-1.5 appearance-none rounded-full cursor-pointer accent-blue-500 ${
                isDark ? 'bg-slate-700' : 'bg-slate-300'
              }`}
            />
            <span className={`text-sm font-semibold w-10 text-right flex-shrink-0 ${
              isDark ? 'text-blue-400' : 'text-blue-600'
            }`}>
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}

        <div className={`flex gap-1 mb-6 rounded-2xl p-1.5 border transition-colors ${
          isDark
            ? 'bg-slate-900/60 border-slate-800'
            : 'bg-slate-100 border-slate-300'
        }`}>
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                tab === t.id
                  ? isDark
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                    : 'bg-blue-500 text-white shadow-md shadow-blue-500/30'
                  : isDark
                    ? 'text-slate-500 hover:text-slate-300'
                    : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {t.icon}
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>

        <div className={`rounded-2xl border p-6 transition-colors backdrop-blur-sm ${
          isDark
            ? 'border-slate-800/80 bg-slate-900/50'
            : 'border-slate-300 bg-slate-50/50'
        }`}>
          {tab === 'image' && (
            <ImageDetection confidence={confidence} onModelLoading={setModelLoading} />
          )}
          {tab === 'webcam' && (
            <WebcamDetection confidence={confidence} onModelLoading={setModelLoading} />
          )}
          {tab === 'video' && (
            <VideoDetection confidence={confidence} onModelLoading={setModelLoading} />
          )}
          {tab === 'log' && <DetectionLog />}
          {tab === 'model' && <ModelInfo />}
        </div>

        <footer className={`mt-6 text-center text-xs ${
          isDark ? 'text-slate-600' : 'text-slate-500'
        }`}>
          All inference runs locally in your browser. No images are uploaded.
        </footer>
      </div>
    </div>
  );
}
