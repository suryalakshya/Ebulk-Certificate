import React, { useRef, useEffect } from 'react';
import { X, CheckCircle, AlertTriangle, Download, Terminal, RefreshCw } from 'lucide-react';

export default function ProgressModal({ isOpen, onClose, jobState }) {
  const terminalEndRef = useRef(null);

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [jobState.logs]);

  if (!isOpen) return null;

  const current = jobState.progress?.current || 0;
  const total = jobState.progress?.total || 1;
  const stage = jobState.progress?.stage || 'Processing';
  const percentage = Math.min(100, Math.round((current / (total || 1)) * 100));

  const isCompleted = jobState.status === 'completed';
  const isFailed = jobState.status === 'failed';

  return (
    <div className="modal-backdrop">
      <div className="modal-card">
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Terminal size={22} style={{ color: 'var(--accent-blue)' }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                {isCompleted ? 'Batch Task Completed' : `${stage}...`}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {jobState.running ? 'Async workers operating...' : 'Process ended.'}
              </div>
            </div>
          </div>

          {!jobState.running && (
            <button className="toolbar-btn" onClick={onClose}>
              <X size={20} />
            </button>
          )}
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Progress Indicator */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: 600 }}>
              <span>{stage}</span>
              <span>
                {current} / {total} ({percentage}%)
              </span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${percentage}%` }} />
            </div>
          </div>

          {/* Stats Cards when completed */}
          {isCompleted && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div style={{ padding: '12px', backgroundColor: 'var(--card-bg)', borderRadius: '8px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-sub)' }}>TOTAL QUEUED</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)' }}>{total}</div>
              </div>
              <div style={{ padding: '12px', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--success)' }}>SUCCESSFUL</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--success)' }}>
                  {jobState.successful?.length || 0}
                </div>
              </div>
              <div style={{ padding: '12px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--danger)' }}>FAILED</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--danger)' }}>
                  {jobState.failed?.length || 0}
                </div>
              </div>
            </div>
          )}

          {/* Terminal Console Log */}
          <div className="terminal-box">
            {jobState.logs && jobState.logs.length > 0 ? (
              jobState.logs.map((log, idx) => (
                <div key={idx} style={{ color: log.includes('✗') ? '#ef4444' : log.includes('✓') ? '#10b981' : '#3b82f6' }}>
                  {log}
                </div>
              ))
            ) : (
              <div style={{ color: 'var(--text-sub)' }}>[System initialized. Awaiting logs...]</div>
            )}
            <div ref={terminalEndRef} />
          </div>

          {/* Action Download Buttons */}
          {isCompleted && (
            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              <a
                href="/api/download-zip"
                download
                className="btn-primary"
                style={{ textDecoration: 'none', flex: 1 }}
              >
                <Download size={18} />
                <span>Download Output ZIP</span>
              </a>

              {jobState.failed && jobState.failed.length > 0 && (
                <a
                  href="/api/download-failed-csv"
                  download
                  className="btn-primary"
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    color: '#ef4444',
                    border: '1px solid rgba(239, 68, 68, 0.4)',
                    textDecoration: 'none',
                    flex: 1,
                  }}
                >
                  <AlertTriangle size={18} />
                  <span>Download Failed CSV</span>
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
