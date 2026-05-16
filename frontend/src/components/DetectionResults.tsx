import type { DetectedObject } from '../lib/api.types';
import { useTheme } from '../lib/theme';

interface Props {
  detections: DetectedObject[];
}

export default function DetectionResults({ detections }: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  if (detections.length === 0) return null;

  const counts: Record<string, number> = {};
  for (const d of detections) {
    counts[d.label] = (counts[d.label] ?? 0) + 1;
  }

  return (
    <div className={`rounded-2xl border overflow-hidden transition-colors ${
      isDark
        ? 'border-slate-700 bg-slate-800/50'
        : 'border-slate-300 bg-slate-100/50'
    }`}>
      <div className={`px-4 py-3 border-b flex items-center justify-between ${
        isDark ? 'border-slate-700/60' : 'border-slate-300'
      }`}>
        <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-200' : 'text-slate-900'}`}>
          Detection Results
        </h3>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
          isDark
            ? 'bg-blue-500/20 text-blue-300'
            : 'bg-blue-100 text-blue-700'
        }`}>
          {detections.length} object{detections.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
        {detections.map((det, i) => {
          const pct = det.confidence * 100;
          const hue = labelHue(det.label);
          return (
            <div
              key={i}
              className={`flex items-center gap-3 p-2.5 rounded-xl border transition-colors ${
                isDark
                  ? 'bg-slate-900/60 border-slate-700/40'
                  : 'bg-white border-slate-300'
              }`}
            >
              <div
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: `hsl(${hue}, 85%, 55%)` }}
              />
              <span className={`text-sm font-medium capitalize flex-1 ${
                isDark ? 'text-slate-200' : 'text-slate-900'
              }`}>
                {det.label}
              </span>
              <div className="flex items-center gap-2">
                <div className={`w-20 h-1.5 rounded-full overflow-hidden ${
                  isDark ? 'bg-slate-700' : 'bg-slate-300'
                }`}>
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: `hsl(${hue}, 85%, 55%)`,
                    }}
                  />
                </div>
                <span className={`text-xs w-10 text-right ${
                  isDark ? 'text-slate-400' : 'text-slate-600'
                }`}>
                  {pct.toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {Object.keys(counts).length > 1 && (
        <div className="px-4 pb-4 flex flex-wrap gap-2">
          {Object.entries(counts).map(([label, count]) => (
            <span
              key={label}
              className={`text-xs px-2.5 py-1 rounded-full ${
                isDark
                  ? 'bg-slate-700/60 text-slate-300'
                  : 'bg-slate-300 text-slate-700'
              }`}
            >
              {count}x {label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function labelHue(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash) % 360;
}
