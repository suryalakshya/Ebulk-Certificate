import React, { useRef } from 'react';
import { LayoutGrid, Upload, FileSpreadsheet, Send, LogOut } from 'lucide-react';

export default function Sidebar({
  templateFilename,
  onTemplateUpload,
  csvFilename,
  csvRowsCount,
  csvHeaders,
  onCsvUpload,
  fields,
  onToggleField,
  selectedFieldKey,
  onSelectField,
  onUpdateField,
  emailConfig,
  onUpdateEmailConfig,
  onStartGeneration,
  isJobRunning,
  onLogout,
}) {
  const templateInputRef = useRef(null);
  const csvInputRef = useRef(null);

  const selectedField = fields.find((f) => f.field === selectedFieldKey) || fields[0];

  const colorOptions = [
    { label: 'Black', hex: '#000000' },
    { label: 'Navy Blue', hex: '#0F2042' },
    { label: 'White', hex: '#FFFFFF' },
    { label: 'Crimson Red', hex: '#C0392B' },
    { label: 'Gold', hex: '#D4AF37' },
  ];

  return (
    <aside className="sidebar">
      {/* App Header matching screenshot */}
      <div className="sidebar-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="sidebar-title">
            <LayoutGrid size={22} style={{ color: 'var(--accent-blue)' }} />
            <span>Certificate Generator</span>
          </div>

          {onLogout && (
            <button
              onClick={onLogout}
              className="toolbar-btn"
              title="Logout"
              style={{ color: '#ef4444' }}
            >
              <LogOut size={18} />
            </button>
          )}
        </div>
        <div className="sidebar-subtitle">Bulk generate certificates from CSV data</div>
      </div>

      {/* FILES section */}
      <div className="sidebar-section">
        <div className="section-label">Files</div>

        {/* Upload Template Card */}
        <input
          type="file"
          ref={templateInputRef}
          accept="image/png, image/jpeg, image/webp"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              onTemplateUpload(e.target.files[0]);
            }
          }}
        />
        <div className="dropzone-card" onClick={() => templateInputRef.current?.click()}>
          <Upload size={24} className="dropzone-icon" />
          <div className="dropzone-text">Upload Template Image</div>
          {templateFilename && (
            <div className="dropzone-subtext">{templateFilename} loaded</div>
          )}
        </div>

        {/* Upload CSV Card */}
        <input
          type="file"
          ref={csvInputRef}
          accept=".csv"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              onCsvUpload(e.target.files[0]);
            }
          }}
        />
        <div className="dropzone-card" onClick={() => csvInputRef.current?.click()}>
          <FileSpreadsheet size={24} className="dropzone-icon" />
          <div className="dropzone-text">Upload CSV Data</div>
          {csvRowsCount > 0 && (
            <div className="dropzone-subtext">{csvRowsCount} rows</div>
          )}
        </div>
      </div>

      {/* TEXT POSITIONING section matching screenshot */}
      <div className="sidebar-section">
        <div className="section-label">Text Positioning</div>

        {csvRowsCount === 0 && fields.length === 0 ? (
          <div style={{ fontSize: '0.85rem', color: '#9ca3af', fontStyle: 'italic', padding: '8px 0' }}>
            Upload a CSV to configure text positions.
          </div>
        ) : (
          <>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
              Select a field, then click the certificate to place it.
            </div>

            {/* Field Selection Toggles */}
            {fields.map((f) => (
              <div
                key={f.field}
                className={`field-item ${selectedFieldKey === f.field ? 'active' : ''}`}
                onClick={() => onSelectField(f.field)}
              >
                <div className="field-left">
                  <input
                    type="checkbox"
                    className="checkbox-custom"
                    checked={f.enabled}
                    onChange={(e) => {
                      e.stopPropagation();
                      onToggleField(f.field);
                    }}
                  />
                  <span className="field-title">{f.label || f.field}</span>
                </div>

                {/* Color Palette Badges matching screenshot */}
                <div className="color-badge-list">
                  {colorOptions.map((c) => (
                    <div
                      key={c.hex}
                      className={`color-badge ${f.color === c.hex ? 'selected' : ''}`}
                      style={{ backgroundColor: c.hex }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onUpdateField(f.field, { color: c.hex });
                      }}
                      title={c.label}
                    />
                  ))}
                </div>
              </div>
            ))}

            {/* Dynamic Controls for currently selected field */}
            {selectedField && selectedField.enabled && (
              <div style={{ marginTop: '16px', padding: '12px', backgroundColor: 'var(--card-bg)', borderRadius: '8px' }}>
                <div className="input-row">
                  <div className="form-group">
                    <label className="form-label">X Coordinate</label>
                    <input
                      type="number"
                      className="form-input"
                      value={selectedField.x}
                      onChange={(e) => onUpdateField(selectedField.field, { x: parseInt(e.target.value) || 0 })}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Y Coordinate</label>
                    <input
                      type="number"
                      className="form-input"
                      value={selectedField.y}
                      onChange={(e) => onUpdateField(selectedField.field, { y: parseInt(e.target.value) || 0 })}
                    />
                  </div>
                </div>

                <div className="input-row">
                  <div className="form-group">
                    <label className="form-label">Font Size</label>
                    <input
                      type="number"
                      className="form-input"
                      value={selectedField.size}
                      onChange={(e) => onUpdateField(selectedField.field, { size: parseInt(e.target.value) || 12 })}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Align</label>
                    <select
                      className="form-select"
                      value={selectedField.align}
                      onChange={(e) => onUpdateField(selectedField.field, { align: e.target.value })}
                    >
                      <option value="center">center</option>
                      <option value="left">left</option>
                      <option value="right">right</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Font Style</label>
                  <select
                    className="form-select"
                    value={selectedField.font_path}
                    onChange={(e) => onUpdateField(selectedField.field, { font_path: e.target.value })}
                  >
                    <option value="arial.ttf">Arial (sans-serif)</option>
                    <option value="georgia.ttf">Georgia (serif)</option>
                    <option value="times.ttf">Times New Roman (serif)</option>
                    <option value="courier.ttf">Courier (monospace)</option>
                  </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
                  <input
                    type="checkbox"
                    id="boldToggle"
                    className="checkbox-custom"
                    checked={selectedField.bold}
                    onChange={(e) => onUpdateField(selectedField.field, { bold: e.target.checked })}
                  />
                  <label htmlFor="boldToggle" style={{ fontSize: '0.85rem', cursor: 'pointer' }}>
                    Bold Text
                  </label>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* OUTPUT FORMAT section */}
      <div className="sidebar-section">
        <div className="section-label">Output Format</div>
        <div className="form-group">
          <label className="form-label">Export File Format</label>
          <select
            className="form-select"
            value={emailConfig.output_format || 'both'}
            onChange={(e) => onUpdateEmailConfig({ output_format: e.target.value })}
          >
            <option value="both">Both PNG & PDF (.png + .pdf)</option>
            <option value="pdf">PDF Document (.pdf)</option>
            <option value="png">PNG Image (.png)</option>
            <option value="jpg">JPEG Image (.jpg)</option>
          </select>
        </div>
      </div>

      {/* EMAIL CONFIG section matching screenshot */}
      <div className="sidebar-section">
        <div className="section-label">Email</div>

        <div className="form-group">
          <label className="form-label">Recipient column</label>
          <select
            className="form-select"
            value={emailConfig.recipient_column}
            onChange={(e) => onUpdateEmailConfig({ recipient_column: e.target.value })}
          >
            {csvHeaders.length > 0 ? (
              csvHeaders.map((h) => (
                <option key={h} value={h}>
                  {h}
                </option>
              ))
            ) : (
              <option value="email">email</option>
            )}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">From name</label>
          <input
            type="text"
            className="form-input"
            value={emailConfig.brevo_from_name}
            onChange={(e) => onUpdateEmailConfig({ brevo_from_name: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label">From email (verified Brevo sender)</label>
          <select
            className="form-select"
            value={emailConfig.brevo_from_email || 'suryalbrcem9@gmail.com'}
            onChange={(e) => onUpdateEmailConfig({ brevo_from_email: e.target.value })}
          >
            <option value="suryalbrcem9@gmail.com">suryalbrcem9@gmail.com</option>
            <option value="poojithakonduri778@gmail.com">poojithakonduri778@gmail.com</option>
            <option value="communityservice202526@gmail.com">communityservice202526@gmail.com</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Subject</label>
          <input
            type="text"
            className="form-input"
            value={emailConfig.email_subject}
            onChange={(e) => onUpdateEmailConfig({ email_subject: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Body — use {'{column}'} placeholders</label>
          <textarea
            className="form-textarea"
            value={emailConfig.email_body}
            onChange={(e) => onUpdateEmailConfig({ email_body: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Delay between emails (ms)</label>
          <input
            type="number"
            className="form-input"
            value={Math.round(emailConfig.email_interval_seconds * 1000)}
            onChange={(e) =>
              onUpdateEmailConfig({
                email_interval_seconds: (parseInt(e.target.value) || 3000) / 1000,
              })
            }
          />
        </div>
      </div>

      {/* Action Footer */}
      <div style={{ padding: '20px 24px', marginTop: 'auto', background: 'var(--panel-bg)' }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-sub)', marginBottom: '10px' }}>
          {csvRowsCount > 300
            ? '300 rows loaded (capped at 300 max limit)'
            : csvRowsCount > 0
            ? `${csvRowsCount} rows loaded`
            : '0 rows loaded'}
        </div>
        <button
          className="btn-primary"
          onClick={onStartGeneration}
          disabled={isJobRunning || csvRowsCount === 0 || !templateFilename}
        >
          <Send size={18} />
          <span>{isJobRunning ? 'Processing Batch...' : 'Generate Certificates'}</span>
        </button>
      </div>
    </aside>
  );
}
