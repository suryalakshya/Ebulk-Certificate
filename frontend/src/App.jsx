import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import CanvasPreview from './components/CanvasPreview';
import ProgressModal from './components/ProgressModal';
import LoginPage from './components/LoginPage';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return !!localStorage.getItem('auth_token');
  });

  const [templateUrl, setTemplateUrl] = useState(null);
  const [templateFilename, setTemplateFilename] = useState(null);

  const [csvRows, setCsvRows] = useState([]);
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [csvFilename, setCsvFilename] = useState(null);
  const [currentRowIndex, setCurrentRowIndex] = useState(0);

  // Field positioning state - empty on start until CSV is loaded
  const [fields, setFields] = useState([]);
  const [selectedFieldKey, setSelectedFieldKey] = useState(null);

  // Email Config state
  const [emailConfig, setEmailConfig] = useState({
    brevo_smtp_host: 'smtp-relay.brevo.com',
    brevo_smtp_port: 2525,
    brevo_smtp_user: '',
    brevo_smtp_password: '',
    brevo_from_email: 'suryalbrcem9@gmail.com',
    brevo_from_name: 'ACG Organizing Committee',
    recipient_column: 'email',
    email_subject: 'Certificate of Participation - ACG Poster Presentation 2026',
    email_body:
      'Dear {name},\n\n' +
      'Thank you for your participation in the ACG Poster Presentation event organized by the Department of Computer Science and Engineering at LBRCE.\n\n' +
      'Please find attached your Certificate of Participation for the event.\n\n' +
      'Participant Details:\n' +
      'Name: {name}\n' +
      'Roll Number: {roll_number}\n' +
      'Certificate ID: {certificate_id}\n\n' +
      'This certificate acknowledges your contribution to the event.\n\n' +
      'If you have any questions or need any assistance, please feel free to contact us.\n\n' +
      'Best regards,\n' +
      'ACG Organizing Committee\n' +
      'Department of Computer Science and Engineering\n' +
      'LBRCE',
    max_emails: 300,
    certificate_workers: 10,
    smtp_workers: 5,
    email_interval_seconds: 3.0,
    send_email: true,
    output_format: 'both',
  });

  // Progress & Job State
  const [jobState, setJobState] = useState({
    running: false,
    status: 'idle',
    logs: [],
    progress: { current: 0, total: 0, stage: '' },
    successful: [],
    failed: [],
  });
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Reset session on mount so page reloads start clean without previous uploads
  useEffect(() => {
    fetch('/api/reset-session', { method: 'POST' })
      .then(() => fetch('/api/status'))
      .then((res) => res.json())
      .then((data) => {
        if (data.config_defaults) {
          setEmailConfig((prev) => ({
            ...prev,
            brevo_from_email: data.config_defaults.brevo_from_email || prev.brevo_from_email,
            brevo_from_name: data.config_defaults.brevo_from_name || prev.brevo_from_name,
            brevo_smtp_user: data.config_defaults.brevo_smtp_user || prev.brevo_smtp_user,
          }));
        }
      })
      .catch((err) => console.error('Error resetting session:', err));
  }, []);

  // Poll job progress when job is running
  useEffect(() => {
    let interval = null;
    if (jobState.running) {
      interval = setInterval(() => {
        fetch('/api/job-progress')
          .then((res) => res.json())
          .then((state) => {
            setJobState(state);
            if (!state.running) {
              clearInterval(interval);
            }
          })
          .catch((err) => console.error('Error polling job progress:', err));
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [jobState.running]);

  // File Upload Handlers
  const handleTemplateUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload-template', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      setTemplateFilename(data.filename || file.name);
      setTemplateUrl('/api/template-image?t=' + Date.now());
    } catch (err) {
      alert('Error uploading template image: ' + err.message);
    }
  };

  const handleCsvUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload-csv', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('CSV upload failed');
      const data = await res.json();
      setCsvRows(data.sample || []);
      const headers = data.headers || [];
      setCsvHeaders(headers);
      setCsvFilename(file.name);
      setCurrentRowIndex(0);

      // Auto generate initial text position field specs for CSV headers
      const defaultFieldsSpec = [
        {
          field: 'name',
          label: 'Full name',
          x: 1000,
          y: 640,
          size: 48,
          align: 'center',
          font_path: 'georgia.ttf',
          color: '#0F2042',
          bold: true,
          enabled: true,
        },
        {
          field: 'roll_number',
          label: 'Roll Number',
          x: 540,
          y: 735,
          size: 38,
          align: 'center',
          font_path: 'arial.ttf',
          color: '#000000',
          bold: false,
          enabled: true,
        },
        {
          field: 'email',
          label: 'email',
          x: 1000,
          y: 735,
          size: 32,
          align: 'center',
          font_path: 'arial.ttf',
          color: '#0F2042',
          bold: false,
          enabled: true,
        },
        {
          field: 'certificate_id',
          label: 'certificate_id',
          x: 1760,
          y: 1330,
          size: 20,
          align: 'left',
          font_path: 'arial.ttf',
          color: '#333333',
          bold: false,
          enabled: true,
        },
      ];

      // Merge headers into fields
      const generatedFields = headers.map((h, idx) => {
        const matchingDefault = defaultFieldsSpec.find((df) => df.field.toLowerCase() === h.toLowerCase());
        if (matchingDefault) return matchingDefault;
        return {
          field: h,
          label: h,
          x: 500,
          y: 400 + idx * 80,
          size: 36,
          align: 'center',
          font_path: 'arial.ttf',
          color: '#000000',
          bold: false,
          enabled: true,
        };
      });

      // Always include certificate_id option
      if (!generatedFields.some((f) => f.field === 'certificate_id')) {
        generatedFields.push({
          field: 'certificate_id',
          label: 'certificate_id',
          x: 1760,
          y: 1330,
          size: 20,
          align: 'left',
          font_path: 'arial.ttf',
          color: '#333333',
          bold: false,
          enabled: false,
        });
      }

      setFields(generatedFields);
      if (generatedFields.length > 0) {
        setSelectedFieldKey(generatedFields[0].field);
      }
    } catch (err) {
      alert('Error uploading CSV file: ' + err.message);
    }
  };

  // Field State Handlers
  const handleToggleField = (fieldKey) => {
    setFields((prev) =>
      prev.map((f) => (f.field === fieldKey ? { ...f, enabled: !f.enabled } : f))
    );
  };

  const handleUpdateField = (fieldKey, updates) => {
    setFields((prev) =>
      prev.map((f) => (f.field === fieldKey ? { ...f, ...updates } : f))
    );
  };

  const handleUpdateEmailConfig = (updates) => {
    setEmailConfig((prev) => ({ ...prev, ...updates }));
  };

  // Start Generation Job
  const handleStartGeneration = async () => {
    if (!templateUrl || !templateFilename) {
      alert('Please upload a certificate template image first.');
      return;
    }
    if (csvRows.length === 0) {
      alert('Please upload CSV recipient data first.');
      return;
    }

    const activeFields = fields.filter((f) => f.enabled);
    if (activeFields.length === 0) {
      alert('Please select at least one field to render on the certificate.');
      return;
    }

    const reqPayload = {
      fields: activeFields.map((f) => ({
        field: f.field,
        x: f.x,
        y: f.y,
        size: f.size,
        align: f.align,
        font_path: f.font_path,
        color: f.color,
        bold: f.bold,
      })),
      output_format: emailConfig.output_format || 'both',
      email_config: emailConfig,
    };

    try {
      const res = await fetch('/api/start-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reqPayload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to start job');
      }

      setJobState({
        running: true,
        status: 'processing',
        logs: ['[System] Job starting...'],
        progress: { current: 0, total: csvRows.length || 1, stage: 'Initializing' },
        successful: [],
        failed: [],
      });
      setIsModalOpen(true);
    } catch (err) {
      alert('Error starting job: ' + err.message);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/reset-session', { method: 'POST' });
    } catch (err) {
      console.error('Failed to purge output directory on logout:', err);
    }
    setTemplateUrl(null);
    setTemplateFilename(null);
    setCsvRows([]);
    setCsvHeaders([]);
    setCsvFilename(null);
    setFields([]);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_email');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="app-container">
      {/* Left Controls Sidebar */}
      <Sidebar
        templateFilename={templateFilename}
        onTemplateUpload={handleTemplateUpload}
        csvFilename={csvFilename}
        csvRowsCount={csvRows.length}
        csvHeaders={csvHeaders}
        onCsvUpload={handleCsvUpload}
        fields={fields}
        onToggleField={handleToggleField}
        selectedFieldKey={selectedFieldKey}
        onSelectField={setSelectedFieldKey}
        onUpdateField={handleUpdateField}
        emailConfig={emailConfig}
        onUpdateEmailConfig={handleUpdateEmailConfig}
        onStartGeneration={handleStartGeneration}
        isJobRunning={jobState.running}
        onLogout={handleLogout}
      />

      {/* Main Interactive Canvas Workspace */}
      <CanvasPreview
        templateUrl={templateUrl}
        fields={fields}
        onUpdateField={handleUpdateField}
        selectedFieldKey={selectedFieldKey}
        onSelectField={setSelectedFieldKey}
        csvRows={csvRows}
        currentRowIndex={currentRowIndex}
        onRowChange={setCurrentRowIndex}
      />

      {/* Live Job Progress & Log Modal */}
      <ProgressModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        jobState={jobState}
      />
    </div>
  );
}
