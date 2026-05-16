import { useState, useCallback } from 'react';
import { RefreshCw, Clock, Target, AlertCircle } from 'lucide-react';
import { useTheme } from '../lib/theme';
import { useDetectionLogs } from '../lib/api.hooks';

export default function DetectionLog() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [skip, setSkip] = useState(0);
  const [limit] = useState(10);
  const [selected, setSelected] = useState<string | null>(null);

  const { data: logs, loading, error, refresh } = useDetectionLogs(skip, limit);

  const handlePrevious = useCallback(() => {
    if (skip > 0) setSkip(skip - limit);
  }, [skip, limit]);

  const handleNext = useCallback(() => {
    if (logs.length === limit) setSkip(skip + limit);
  }, [logs.length, skip, limit]);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          {logs.length} detection{logs.length !== 1 ? 's' : ''} (Page {Math.floor(skip / limit) + 1})
        </p>
        <button
          onClick={refresh}
          disabled={loading}
          className={`flex items-center gap-1.5 text-sm disabled:opacity-50 transition-colors ${
            isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
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

      {loading ? (
        <div className="flex flex-col gap-2">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={`h-14 rounded-xl animate-pulse ${isDark ? 'bg-slate-800/60' : 'bg-slate-300/60'}`}
            />
          ))}
        </div>
      ) : logs.length === 0 ? (
        <div
          className={`flex flex-col items-center justify-center py-16 gap-3 ${
            isDark ? 'text-slate-500' : 'text-slate-600'
          }`}
        >
          <Target className="w-10 h-10 opacity-30" />
          <p className="text-sm">No detections logged yet</p>
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-2">
            {logs.map((log) => (
              <button
                key={log.detection_id}
                onClick={() => setSelected(selected === String(log.detection_id) ? null : String(log.detection_id))}
                className={`w-full text-left rounded-xl border transition-all duration-150 overflow-hidden ${
                  selected === String(log.detection_id)
                    ? isDark
                      ? 'border-blue-500/50 bg-blue-950/30'
                      : 'border-blue-400 bg-blue-50'
                    : isDark
                      ? 'border-slate-700/60 bg-slate-800/40 hover:border-slate-600 hover:bg-slate-800/70'
                      : 'border-slate-300 bg-slate-100 hover:border-slate-400 hover:bg-slate-150'
                }`}
              >
                <div className="flex items-center gap-3 px-4 py-3">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                      isDark ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' : 'bg-blue-100 text-blue-700 border-blue-300'
                    }`}
                  >
                    {log.input_type}
                  </span>
                  {log.filename && (
                    <span
                      className={`text-xs truncate flex-1 max-w-[180px] ${isDark ? 'text-slate-400' : 'text-slate-600'}`}
                    >
                      {log.filename}
                    </span>
                  )}
                  <span className={`text-xs flex items-center gap-1 ml-auto ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
                    <Clock className="w-3 h-3" />
                    {formatDate(log.created_at)}
                  </span>
                  <span className={`text-sm font-semibold ml-2 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                    {log.total_objects}
                  </span>
                </div>
              </button>
            ))}
          </div>

          <div className="flex gap-2 mt-4">
            <button
              onClick={handlePrevious}
              disabled={skip === 0 || loading}
              className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 ${
                isDark
                  ? 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
                  : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
              }`}
            >
              ← Previous
            </button>
            <button
              onClick={handleNext}
              disabled={logs.length < limit || loading}
              className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 ${
                isDark
                  ? 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
                  : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
              }`}
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
