import React, { useState, useEffect } from 'react';
import {
  Upload,
  Video,
  FileText,
  Play,
  Pause,
  Download,
  Sparkles,
  CheckCircle2,
  Clock,
  Volume2,
  ArrowRight,
  Layers,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { LanguageSelector } from '../components/LanguageSelector';
import {
  uploadVideo,
  startVideoTranslation,
  triggerDemoVideo,
  getVideoStatus,
  getVideoHistory,
} from '../api';

export function VideoTranslatorPage() {
  const { sourceLang, targetLang, setSourceLang, setTargetLang, swapLanguages } = useAppStore();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeJob, setActiveJob] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [subtitleMode, setSubtitleMode] = useState('dual'); // 'dual' | 'target' | 'source'
  const [historyJobs, setHistoryJobs] = useState([]);
  const [activeSegmentIndex, setActiveSegmentIndex] = useState(0);

  // Load history on mount
  useEffect(() => {
    getVideoHistory()
      .then((jobs) => {
        setHistoryJobs(jobs);
        if (jobs.length > 0 && !activeJob) {
          setActiveJob(jobs[0]);
        }
      })
      .catch((e) => console.log('Video history load notice:', e));
  }, []);

  // Poll video status while processing
  useEffect(() => {
    if (!activeJob || activeJob.status === 'COMPLETED' || activeJob.status === 'FAILED') {
      setIsProcessing(false);
      return;
    }

    setIsProcessing(true);
    const interval = setInterval(async () => {
      try {
        const updated = await getVideoStatus(activeJob.job_id);
        setActiveJob(updated);
        if (updated.status === 'COMPLETED' || updated.status === 'FAILED') {
          setIsProcessing(false);
          clearInterval(interval);
          getVideoHistory().then(setHistoryJobs);
        }
      } catch (e) {
        clearInterval(interval);
        setIsProcessing(false);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [activeJob?.job_id, activeJob?.status]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelected = (file) => {
    setSelectedFile(file);
  };

  const handleStartUploadAndTranslate = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    try {
      const job = await uploadVideo(selectedFile, sourceLang, targetLang);
      setActiveJob(job);
      await startVideoTranslation(job.job_id, sourceLang, targetLang);
    } catch (e) {
      console.error(e);
      setIsProcessing(false);
    }
  };

  const handleRunInstantDemo = async () => {
    setIsProcessing(true);
    try {
      const job = await triggerDemoVideo(sourceLang, targetLang);
      setActiveJob(job);
    } catch (e) {
      console.error(e);
      setIsProcessing(false);
    }
  };

  const stages = [
    { label: 'Video uploaded', threshold: 10 },
    { label: 'Extracting audio', threshold: 25 },
    { label: 'Transcribing speech', threshold: 45 },
    { label: 'Translating with Entity Shield', threshold: 70 },
    { label: 'Generating subtitles & voiceover', threshold: 85 },
    { label: 'Finalizing video', threshold: 95 },
  ];

  return (
    <div className="page-container">
      {/* Header Banner */}
      <div className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
            Video Lesson Translation Studio
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Translate prerecorded classroom videos with synchronized dual subtitles and vernacular audio
          </p>
        </div>
        <button
          className="demo-launch-btn"
          onClick={handleRunInstantDemo}
          disabled={isProcessing}
        >
          <Sparkles size={15} />
          <span>Translate Sample Lesson</span>
        </button>
      </div>

      {/* Language Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px' }}>
        <LanguageSelector
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSourceChange={setSourceLang}
          onTargetChange={setTargetLang}
          onSwap={swapLanguages}
        />
      </div>

      {/* Main Grid: Upload & Progress / Subtitle Player */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {/* Left Column: Upload Box & Stepper */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Drag & Drop Upload Zone */}
          <div
            className="glass-panel"
            style={{
              padding: '32px 24px',
              textAlign: 'center',
              border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--border-color)'}`,
              backgroundColor: dragActive ? 'var(--primary-light)' : 'var(--bg-surface)',
              cursor: 'pointer',
            }}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px auto' }}>
              <Upload size={24} />
            </div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
              Upload Classroom Video
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Drag and drop your lesson file here or click below
            </p>

            <input
              type="file"
              id="video-file-input"
              accept=".mp4,.webm,.mov,.mkv"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
            />

            <label
              htmlFor="video-file-input"
              className="primary-action-btn"
              style={{ display: 'inline-flex', cursor: 'pointer' }}
            >
              Choose Video File
            </label>

            <div style={{ marginTop: '12px', fontSize: '11px', color: 'var(--text-dim)' }}>
              Supported: MP4, WebM, MOV, MKV (Max 250MB)
            </div>

            {selectedFile && (
              <div style={{ marginTop: '16px', padding: '8px 12px', backgroundColor: 'var(--bg-surface-secondary)', borderRadius: 'var(--radius-md)', display: 'inline-flex', alignItems: 'center', gap: '8px', border: '1px solid var(--border-color)' }}>
                <FileText size={14} color="var(--primary)" />
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{selectedFile.name}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  ({(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)
                </span>
              </div>
            )}
          </div>

          {/* Action Trigger Card */}
          <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Pipeline Target
              </span>
              <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                {sourceLang.toUpperCase()} → {targetLang.toUpperCase()}
              </div>
            </div>

            <button
              className="primary-action-btn"
              onClick={handleStartUploadAndTranslate}
              disabled={!selectedFile || isProcessing}
            >
              {isProcessing ? 'Processing Video...' : 'Translate Video'}
            </button>
          </div>

          {/* Processing Progress Checklist */}
          {activeJob && (
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Processing Progress: {activeJob.progress}%
                </span>
                <span className="model-badge">
                  {activeJob.status}
                </span>
              </div>

              {/* Progress Bar */}
              <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden', marginBottom: '16px' }}>
                <div style={{ width: `${activeJob.progress}%`, height: '100%', backgroundColor: 'var(--primary)', transition: 'width 0.3s ease' }} />
              </div>

              {/* Steps */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {stages.map((stage, idx) => {
                  const isDone = activeJob.progress >= stage.threshold;
                  return (
                    <div key={`stage-${idx}`} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: isDone ? 'var(--text-primary)' : 'var(--text-dim)' }}>
                      <CheckCircle2 size={16} color={isDone ? 'var(--success)' : 'var(--border-color)'} />
                      <span style={{ fontWeight: isDone ? 600 : 400 }}>{stage.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Subtitle & Transcript Explorer */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '10px' }}>
            <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Dual Subtitle Preview & Transcripts
            </span>

            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                className={`icon-action-btn ${subtitleMode === 'dual' ? 'selected' : ''}`}
                onClick={() => setSubtitleMode('dual')}
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                Dual
              </button>
              <button
                className={`icon-action-btn ${subtitleMode === 'target' ? 'selected' : ''}`}
                onClick={() => setSubtitleMode('target')}
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                Target
              </button>
              <button
                className={`icon-action-btn ${subtitleMode === 'source' ? 'selected' : ''}`}
                onClick={() => setSubtitleMode('source')}
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                Source
              </button>
            </div>
          </div>

          {activeJob && activeJob.segments && activeJob.segments.length > 0 ? (
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '420px' }}>
              {activeJob.segments.map((seg, idx) => (
                <div
                  key={`seg-${idx}`}
                  style={{
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: activeSegmentIndex === idx ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                    border: `1px solid ${activeSegmentIndex === idx ? 'var(--primary-border)' : 'var(--border-color)'}`,
                    cursor: 'pointer',
                  }}
                  onClick={() => setActiveSegmentIndex(idx)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    <span>Segment #{idx + 1}</span>
                    <span>{seg.start_time || '00:00'} → {seg.end_time || '00:04'}</span>
                  </div>

                  {(subtitleMode === 'dual' || subtitleMode === 'source') && (
                    <p style={{ fontSize: '14px', color: 'var(--text-primary)', marginBottom: '4px' }}>
                      {seg.source_text}
                    </p>
                  )}

                  {(subtitleMode === 'dual' || subtitleMode === 'target') && (
                    <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--primary)' }}>
                      {seg.translated_text}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', textAlign: 'center', minHeight: '200px' }}>
              <p>Upload a classroom video or click "Translate Sample Lesson" to view synchronized dual subtitles.</p>
            </div>
          )}

          {/* Download Subtitles Bar */}
          {activeJob && activeJob.status === 'COMPLETED' && (
            <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)', display: 'flex', gap: '10px' }}>
              <a
                href={`http://localhost:8000/api/video/download/${activeJob.job_id}/srt`}
                target="_blank"
                rel="noreferrer"
                className="icon-action-btn"
                style={{ textDecoration: 'none' }}
              >
                <Download size={14} />
                <span>Download SRT Subtitles</span>
              </a>
              <a
                href={`http://localhost:8000/api/video/download/${activeJob.job_id}/vtt`}
                target="_blank"
                rel="noreferrer"
                className="icon-action-btn"
                style={{ textDecoration: 'none' }}
              >
                <Download size={14} />
                <span>Download WebVTT Subtitles</span>
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
