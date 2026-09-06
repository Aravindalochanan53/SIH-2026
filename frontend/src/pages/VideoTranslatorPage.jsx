import React, { useState, useEffect, useRef } from 'react';
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
  VolumeX,
  ArrowRight,
  Layers,
  Film,
  RotateCcw,
  Check,
  Headphones,
  Radio,
  Music,
  AlertCircle,
  RefreshCw,
  Cpu,
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

const VOICE_LANG_MAP = {
  ta: 'ta-IN',
  ml: 'ml-IN',
  te: 'te-IN',
  kn: 'kn-IN',
  hi: 'hi-IN',
  bn: 'bn-IN',
  mr: 'mr-IN',
  gu: 'gu-IN',
  ur: 'ur-IN',
  en: 'en-IN',
};

const LANG_NAMES = {
  ta: 'Tamil',
  ml: 'Malayalam',
  te: 'Telugu',
  kn: 'Kannada',
  hi: 'Hindi',
  bn: 'Bengali',
  mr: 'Marathi',
  gu: 'Gujarati',
  ur: 'Urdu',
  en: 'English',
  sat: 'Santali',
  hoc: 'Ho',
  unr: 'Mundari',
};

export function VideoTranslatorPage() {
  const { sourceLang, targetLang, setSourceLang, setTargetLang, swapLanguages } = useAppStore();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [activeJob, setActiveJob] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [subtitleMode, setSubtitleMode] = useState('dual'); // 'dual' | 'target' | 'source'
  const [videoTrack, setVideoTrack] = useState('translated'); // 'translated' | 'original'
  const [voiceMode, setVoiceMode] = useState('translated'); // 'translated' (AI dubbing) | 'original'
  const [voiceVolume, setVoiceVolume] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeakingNow, setIsSpeakingNow] = useState(false);
  const [historyJobs, setHistoryJobs] = useState([]);
  const [activeSegmentIndex, setActiveSegmentIndex] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const videoRef = useRef(null);
  const lastSpokenSegmentRef = useRef(-1);
  const completedJobIdRef = useRef(null);

  // Load history on mount
  useEffect(() => {
    getVideoHistory()
      .then((jobs) => {
        setHistoryJobs(jobs);
        if (jobs.length > 0 && !activeJob && !previewUrl) {
          setActiveJob(jobs[0]);
        }
      })
      .catch((e) => console.log('Video history load notice:', e));
  }, []);

  // When activeJob completes, seamlessly transition player to dubbed video stream & start playing with sound
  useEffect(() => {
    if (activeJob && activeJob.status === 'COMPLETED' && activeJob.job_id && completedJobIdRef.current !== activeJob.job_id) {
      completedJobIdRef.current = activeJob.job_id;
      setVideoTrack('translated');
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.currentTime = 0;
          videoRef.current.muted = false;
          videoRef.current.volume = 1.0;
          setIsMuted(false);
          videoRef.current
            .play()
            .then(() => setIsPlaying(true))
            .catch((err) => {
              console.log('Autoplay handled on translation completion:', err);
            });
        }
      }, 300);
    }
  }, [activeJob?.status, activeJob?.job_id]);

  // Poll video status while processing
  useEffect(() => {
    if (!activeJob || activeJob.status === 'COMPLETED' || activeJob.status === 'FAILED') {
      setIsProcessing(false);
      return;
    }

    setIsProcessing(true);
    let consecutiveErrors = 0;
    const interval = setInterval(async () => {
      try {
        const updated = await getVideoStatus(activeJob.job_id);
        consecutiveErrors = 0;
        setActiveJob(updated);
        if (updated.status === 'COMPLETED' || updated.status === 'FAILED') {
          setIsProcessing(false);
          clearInterval(interval);
          getVideoHistory().then(setHistoryJobs);
        }
      } catch (e) {
        consecutiveErrors++;
        console.warn(`Polling notice (${consecutiveErrors}/15):`, e);
        if (consecutiveErrors >= 15) {
          clearInterval(interval);
          setIsProcessing(false);
        }
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [activeJob?.job_id, activeJob?.status]);

  // Clean up blob URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [previewUrl]);

  // Speech synthesis helper for translated voice
  const speakTranslatedSegment = (text, lang) => {
    if (!text || typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const code = (lang || targetLang || 'ml').toLowerCase();
      utterance.lang = VOICE_LANG_MAP[code] || 'hi-IN';
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      utterance.volume = voiceVolume;
      utterance.onstart = () => setIsSpeakingNow(true);
      utterance.onend = () => {
        setIsSpeakingNow(false);
        if (videoRef.current && !videoRef.current.muted) {
          videoRef.current.volume = 1.0;
        }
      };
      utterance.onerror = () => {
        setIsSpeakingNow(false);
        if (videoRef.current && !videoRef.current.muted) {
          videoRef.current.volume = 1.0;
        }
      };
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('Speech synthesis notice:', e);
      setIsSpeakingNow(false);
      if (videoRef.current && !videoRef.current.muted) {
        videoRef.current.volume = 1.0;
      }
    }
  };

  // Upload & start video translation pipeline
  const startUploadAndTranslateFile = async (file) => {
    if (!file) return;
    setIsProcessing(true);
    setUploadError('');
    try {
      const job = await uploadVideo(file, sourceLang, targetLang);
      setActiveJob(job);
      await startVideoTranslation(job.job_id, sourceLang, targetLang);
    } catch (e) {
      console.error('Video upload/translate error:', e);
      setUploadError(e.message || 'Failed to upload and translate video. Please check backend server.');
      setIsProcessing(false);
    }
  };

  // Handle local file selection: immediately load on screen & run playback with sound
  const handleFileSelected = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setUploadError('');
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    const localUrl = URL.createObjectURL(file);
    setPreviewUrl(localUrl);
    setActiveJob(null); // Clear previous history job so player points directly to uploaded video
    lastSpokenSegmentRef.current = -1;

    // Attempt playback with full sound enabled
    setTimeout(() => {
      if (videoRef.current) {
        videoRef.current.currentTime = 0;
        videoRef.current.muted = false;
        videoRef.current.volume = 1.0;
        setIsMuted(false);
        videoRef.current
          .play()
          .then(() => setIsPlaying(true))
          .catch(() => {
            // Autoplay policy fallback: if browser prevents unmuted autoplay, mute temporarily & let user unmute
            if (videoRef.current) {
              videoRef.current.muted = true;
              setIsMuted(true);
              videoRef.current
                .play()
                .then(() => setIsPlaying(true))
                .catch(() => {});
            }
          });
      }
    }, 100);

    // Automatically trigger upload & voice translation
    startUploadAndTranslateFile(file);
  };

  const handleToggleMute = () => {
    if (!videoRef.current) return;
    const nextMuted = !videoRef.current.muted;
    videoRef.current.muted = nextMuted;
    if (!nextMuted) {
      videoRef.current.volume = 1.0;
    }
    setIsMuted(nextMuted);
  };

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

  const handleManualRefreshStatus = async () => {
    if (!activeJob?.job_id) return;
    try {
      const updated = await getVideoStatus(activeJob.job_id);
      setActiveJob(updated);
      if (updated.status === 'COMPLETED' || updated.status === 'FAILED') {
        setIsProcessing(false);
        getVideoHistory().then(setHistoryJobs);
      }
    } catch (err) {
      console.warn('Manual refresh notice:', err);
    }
  };

  const handleRunInstantDemo = async () => {
    setIsProcessing(true);
    setUploadError('');
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl('');
    }
    setSelectedFile(null);
    lastSpokenSegmentRef.current = -1;
    try {
      const job = await triggerDemoVideo(sourceLang, targetLang);
      setActiveJob(job);
      if (videoRef.current) {
        videoRef.current.muted = false;
        videoRef.current.volume = 1.0;
        setIsMuted(false);
      }
    } catch (e) {
      console.error(e);
      setUploadError(e.message || 'Demo video generation failed');
      setIsProcessing(false);
    }
  };

  // Switch between dubbed stream (with embedded neural AI voice) and original stream
  const switchVideoTrack = (track) => {
    const savedTime = videoRef.current ? videoRef.current.currentTime : 0;
    const wasPlaying = isPlaying;
    setVideoTrack(track);
    setTimeout(() => {
      if (videoRef.current) {
        videoRef.current.currentTime = savedTime;
        if (track === 'translated') {
          videoRef.current.volume = 1.0;
          if ('speechSynthesis' in window) window.speechSynthesis.cancel();
          setIsSpeakingNow(false);
        }
        if (wasPlaying) {
          videoRef.current.play().catch(() => {});
        }
      }
    }, 120);
  };

  // Sync active segment with video time and trigger synchronized voice translation
  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const curr = videoRef.current.currentTime;
    setCurrentTime(curr);

    if (activeJob && activeJob.segments && activeJob.segments.length > 0) {
      const foundIdx = activeJob.segments.findIndex(
        (s) => curr >= (s.start_seconds || 0) && curr <= (s.end_seconds || 9999)
      );
      if (foundIdx !== -1) {
        if (foundIdx !== activeSegmentIndex) {
          setActiveSegmentIndex(foundIdx);
        }

        // When playing dubbed stream (videoTrack === 'translated'), the video ALREADY has the
        // high-quality neural translated voice muxed into its audio track!
        // We ensure full volume and skip browser Web Speech API.
        if (videoTrack === 'translated') {
          if (videoRef.current && !videoRef.current.muted && videoRef.current.volume < 0.95) {
            videoRef.current.volume = 1.0;
          }
        } else if (voiceMode === 'translated' && foundIdx !== lastSpokenSegmentRef.current) {
          lastSpokenSegmentRef.current = foundIdx;
          const seg = activeJob.segments[foundIdx];
          const textToSpeak = seg.target_text || seg.translated_text;
          if (textToSpeak) {
            // Duck background video audio slightly so translated voice is crisp
            if (videoRef.current && !videoRef.current.muted) {
              videoRef.current.volume = 0.25;
            }
            speakTranslatedSegment(textToSpeak, activeJob.target_language || targetLang);
          }
        }
      }
    }
  };

  // Jump video to segment timestamp
  const handleSeekToSegment = (seg, idx) => {
    setActiveSegmentIndex(idx);
    lastSpokenSegmentRef.current = idx;
    if (videoRef.current) {
      videoRef.current.currentTime = seg.start_seconds || 0;
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
    if (videoTrack !== 'translated' && voiceMode === 'translated') {
      const textToSpeak = seg.target_text || seg.translated_text;
      if (textToSpeak) {
        if (videoRef.current && !videoRef.current.muted) {
          videoRef.current.volume = 0.25;
        }
        speakTranslatedSegment(textToSpeak, activeJob?.target_language || targetLang);
      }
    }
  };

  // Dedicated button to listen to a specific segment voice
  const handlePlaySegmentVoice = (seg, e) => {
    e.stopPropagation();
    const textToSpeak = seg.target_text || seg.translated_text;
    if (textToSpeak) {
      speakTranslatedSegment(textToSpeak, activeJob?.target_language || targetLang);
    }
  };

  const handlePause = () => {
    setIsPlaying(false);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeakingNow(false);
    }
  };

  const handlePlay = () => {
    setIsPlaying(true);
    if (videoRef.current && videoRef.current.muted && isMuted) {
      // User explicitly interacted, can unmute
      videoRef.current.muted = false;
      videoRef.current.volume = 1.0;
      setIsMuted(false);
    }
  };

  const activeSegment = activeJob?.segments?.[activeSegmentIndex];

  const currentVideoSource = previewUrl
    ? (activeJob?.status === 'COMPLETED' && videoTrack === 'translated' && activeJob?.job_id
        ? `/api/video/stream/${activeJob.job_id}/translated`
        : previewUrl)
    : (activeJob && activeJob.job_id
        ? `/api/video/stream/${activeJob.job_id}/${videoTrack}`
        : '');

  const stages = [
    { label: 'Video uploaded & verified on screen', threshold: 10 },
    { label: 'Extracting 16kHz audio track', threshold: 25 },
    { label: 'Faster-Whisper speech transcription', threshold: 45 },
    { label: 'TRANSLARA AI vernacular translation', threshold: 65 },
    { label: 'Synchronized WebVTT & SRT subtitle generation', threshold: 75 },
    { label: 'Synthesizing translated voice audio (Dubbing)', threshold: 88 },
    { label: 'Web-streamable video finalization with voice', threshold: 95 },
  ];

  return (
    <div className="page-container">
      {/* Header Banner */}
      <div className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
              <Film size={18} />
            </div>
            <h1 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              Training Video Studio & Voice Translation
            </h1>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
            Upload videos to immediately play on screen with audio, transcribe dialogue, and translate voice into your target language.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            className="demo-launch-btn"
            onClick={handleRunInstantDemo}
            disabled={isProcessing}
          >
            <Sparkles size={15} />
            <span>Translate Sample Training Video</span>
          </button>
        </div>
      </div>

      {/* Language Selector Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px' }}>
        <LanguageSelector
          sourceLang={sourceLang}
          targetLang={targetLang}
          onSourceChange={setSourceLang}
          onTargetChange={setTargetLang}
          onSwap={swapLanguages}
        />
      </div>

      {/* Error Alert if Any */}
      {uploadError && (
        <div className="form-error" style={{ padding: '12px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={18} />
            <span>{uploadError}</span>
          </div>
          <button
            onClick={() => selectedFile && startUploadAndTranslateFile(selectedFile)}
            className="icon-action-btn"
            style={{ fontSize: '11px', padding: '4px 10px' }}
          >
            <RefreshCw size={12} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 1fr) minmax(380px, 1.3fr)', gap: '20px' }}>
        {/* Left Column: Upload & Processing Stepper */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Drag & Drop Upload Card */}
          <div
            className="glass-panel"
            style={{
              padding: '32px 24px',
              textAlign: 'center',
              border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--border-color)'}`,
              backgroundColor: dragActive ? 'rgba(37, 99, 235, 0.05)' : 'var(--bg-surface)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '14px',
              backgroundColor: 'rgba(37, 99, 235, 0.08)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 14px auto',
            }}>
              <Upload size={26} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
              Upload Training Video File
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '18px' }}>
              Drop your video here to immediately play on screen with audio and translate into {LANG_NAMES[targetLang] || 'Target Language'}
            </p>

            <input
              type="file"
              id="video-file-input"
              accept=".mp4,.webm,.mov,.mkv,.avi,.m4v"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
            />

            <label
              htmlFor="video-file-input"
              className="gradient-btn"
              style={{ display: 'inline-flex', cursor: 'pointer', margin: '0 auto' }}
            >
              Choose Video File
            </label>

            <div style={{ marginTop: '12px', fontSize: '11px', color: 'var(--text-muted)' }}>
              Supports MP4, WebM, MOV, MKV of any duration
            </div>

            {selectedFile && (
              <div style={{
                marginTop: '16px',
                padding: '10px 14px',
                backgroundColor: 'var(--bg-surface-secondary)',
                borderRadius: 'var(--radius-md)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '10px',
                border: '1px solid var(--border-color)',
                textAlign: 'left',
              }}>
                <FileText size={16} color="var(--primary)" />
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {selectedFile.name}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB • Playing on screen with audio
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Trigger Card */}
          <div className="glass-panel" style={{ padding: '18px 22px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Translation Direction
              </span>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                {sourceLang.toUpperCase()} → {targetLang.toUpperCase()} ({LANG_NAMES[targetLang] || 'Target Language'})
              </div>
            </div>

            <button
              className="gradient-btn"
              onClick={() => selectedFile && startUploadAndTranslateFile(selectedFile)}
              disabled={!selectedFile || isProcessing}
            >
              {isProcessing ? 'Translating Voice...' : 'Translate Video Voice'}
            </button>
          </div>

          {/* Processing Progress Stepper */}
          {activeJob && (
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Processing: {activeJob.progress}%
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    onClick={handleManualRefreshStatus}
                    className="icon-action-btn"
                    style={{ fontSize: '11px', padding: '3px 8px', display: 'flex', alignItems: 'center', gap: '4px' }}
                    title="Check latest progress from server"
                  >
                    <RefreshCw size={11} />
                    <span>Check Status</span>
                  </button>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: activeJob.status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(37, 99, 235, 0.1)',
                    color: activeJob.status === 'COMPLETED' ? 'var(--success)' : 'var(--primary)',
                  }}>
                    {activeJob.status}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-surface-secondary)', borderRadius: '4px', overflow: 'hidden', marginBottom: '16px', border: '1px solid var(--border-color)' }}>
                <div style={{
                  width: `${activeJob.progress}%`,
                  height: '100%',
                  background: 'var(--gradient-primary)',
                  transition: 'width 0.4s ease',
                }} />
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px', fontStyle: 'italic' }}>
                {activeJob.current_stage}
              </div>

              {/* Pipeline Steps */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {stages.map((stage, idx) => {
                  const isDone = activeJob.progress >= stage.threshold;
                  return (
                    <div key={`stage-${idx}`} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: isDone ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                      <CheckCircle2 size={16} color={isDone ? 'var(--success)' : 'var(--border-color)'} />
                      <span style={{ fontWeight: isDone ? 600 : 400 }}>{stage.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Video History */}
          {historyJobs.length > 0 && (
            <div className="glass-panel" style={{ padding: '18px 20px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>
                Recent Video Translations
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {historyJobs.slice(0, 3).map((job) => (
                  <div
                    key={job.job_id}
                    onClick={() => {
                      setActiveJob(job);
                      if (previewUrl && previewUrl.startsWith('blob:')) {
                        URL.revokeObjectURL(previewUrl);
                        setPreviewUrl('');
                      }
                      setSelectedFile(null);
                      lastSpokenSegmentRef.current = -1;
                      setVideoTrack('translated');
                      setTimeout(() => {
                        if (videoRef.current) {
                          videoRef.current.currentTime = 0;
                          videoRef.current.muted = false;
                          videoRef.current.volume = 1.0;
                          setIsMuted(false);
                          videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
                        }
                      }, 180);
                    }}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: activeJob?.job_id === job.job_id ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                      border: `1px solid ${activeJob?.job_id === job.job_id ? 'var(--primary-border)' : 'var(--border-color)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                      {job.filename}
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: 600 }}>
                      {job.source_language.toUpperCase()} → {job.target_language.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Interactive Video Player & Subtitle Explorer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Video Player Card */}
          <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Video size={18} color="var(--primary)" />
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Interactive Video Player
                </span>
              </div>

              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                {/* Audio Unmute/Mute Toggle */}
                <button
                  onClick={handleToggleMute}
                  className={`icon-action-btn ${isMuted ? 'selected' : ''}`}
                  style={{
                    fontSize: '11px',
                    padding: '4px 10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    backgroundColor: isMuted ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                    color: isMuted ? '#EF4444' : '#10B981',
                    border: `1px solid ${isMuted ? '#EF4444' : '#10B981'}`,
                  }}
                  title="Toggle video sound"
                >
                  {isMuted ? <VolumeX size={13} /> : <Volume2 size={13} />}
                  <span>{isMuted ? 'Muted (Unmute)' : 'Sound On'}</span>
                </button>

                {activeJob && activeJob.status === 'COMPLETED' && (
                  <>
                    <button
                      onClick={() => switchVideoTrack('translated')}
                      className={`icon-action-btn ${videoTrack === 'translated' ? 'selected' : ''}`}
                      style={{ fontSize: '11px', padding: '4px 10px', fontWeight: 700 }}
                    >
                      Dubbed Stream (AI Voice)
                    </button>
                    <button
                      onClick={() => switchVideoTrack('original')}
                      className={`icon-action-btn ${videoTrack === 'original' ? 'selected' : ''}`}
                      style={{ fontSize: '11px', padding: '4px 10px', fontWeight: 600 }}
                    >
                      Original Stream
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Translation Completed Banner */}
            {activeJob && activeJob.status === 'COMPLETED' && (
              <div style={{
                padding: '10px 14px',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#10B981',
                fontSize: '12px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '12px',
                flexWrap: 'wrap',
                gap: '8px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={16} />
                  <span>
                    {videoTrack === 'translated'
                      ? `Playing AI Dubbed Video in ${LANG_NAMES[activeJob.target_language] || activeJob.target_language.toUpperCase()} with dual subtitles.`
                      : `Playing Original Video. Click "Dubbed Stream" to hear translated AI voice.`}
                  </span>
                </div>
                <button
                  onClick={() => {
                    if (videoRef.current) {
                      videoRef.current.currentTime = 0;
                      videoRef.current.muted = false;
                      videoRef.current.volume = 1.0;
                      setIsMuted(false);
                      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
                    }
                  }}
                  style={{
                    backgroundColor: '#10B981',
                    color: '#FFFFFF',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '5px 12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <Play size={12} fill="#fff" />
                  <span>Play from Start</span>
                </button>
              </div>
            )}

            {/* Video Screen with Subtitle Overlay */}
            <div style={{
              position: 'relative',
              width: '100%',
              backgroundColor: '#0F172A',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              minHeight: '280px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {currentVideoSource ? (
                <video
                  ref={videoRef}
                  src={currentVideoSource}
                  controls
                  playsInline
                  onTimeUpdate={handleTimeUpdate}
                  onPlay={handlePlay}
                  onPause={handlePause}
                  style={{ width: '100%', maxHeight: '380px', display: 'block' }}
                />
              ) : (
                <div style={{ color: '#94A3B8', textAlign: 'center', padding: '40px 20px' }}>
                  <Video size={36} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                  <p style={{ margin: 0, fontSize: '13px' }}>Upload a video file above to immediately view and play on screen with audio</p>
                </div>
              )}

              {/* Prominent Unmute Notice if Autoplay was started muted by Browser Policy */}
              {isMuted && currentVideoSource && (
                <button
                  type="button"
                  onClick={handleToggleMute}
                  style={{
                    position: 'absolute',
                    top: '16px',
                    right: '16px',
                    backgroundColor: '#EF4444',
                    color: '#FFFFFF',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: '24px',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    boxShadow: '0 4px 14px rgba(239, 68, 68, 0.4)',
                    zIndex: 10,
                  }}
                >
                  <VolumeX size={15} />
                  <span>Audio Muted — Click to Unmute Sound 🔊</span>
                </button>
              )}

              {/* Dynamic Subtitle Overlay Bar */}
              {activeSegment && isPlaying && (
                <div style={{
                  position: 'absolute',
                  bottom: '60px',
                  left: '20px',
                  right: '20px',
                  backgroundColor: 'rgba(15, 23, 42, 0.88)',
                  backdropFilter: 'blur(8px)',
                  color: '#FFFFFF',
                  padding: '10px 16px',
                  borderRadius: '8px',
                  textAlign: 'center',
                  pointerEvents: 'none',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  zIndex: 4,
                }}>
                  {(subtitleMode === 'dual' || subtitleMode === 'source') && (
                    <div style={{ fontSize: '13px', opacity: 0.85, marginBottom: subtitleMode === 'dual' ? '2px' : '0' }}>
                      {activeSegment.source_text}
                    </div>
                  )}
                  {(subtitleMode === 'dual' || subtitleMode === 'target') && (
                    <div style={{ fontSize: '15px', fontWeight: 700, color: '#38BDF8' }}>
                      {activeSegment.target_text || activeSegment.translated_text}
                    </div>
                  )}
                </div>
              )}

              {/* Active Voice Dubbing Indicator */}
              {isSpeakingNow && (
                <div style={{
                  position: 'absolute',
                  top: '14px',
                  left: '14px',
                  backgroundColor: 'rgba(16, 185, 129, 0.95)',
                  color: '#FFFFFF',
                  padding: '5px 12px',
                  borderRadius: '20px',
                  fontSize: '11px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                  backdropFilter: 'blur(4px)',
                  zIndex: 5,
                }}>
                  <Volume2 size={14} style={{ animation: 'pulse 1s infinite' }} />
                  <span>Speaking in {LANG_NAMES[activeJob?.target_language || targetLang] || 'Target Language'}</span>
                </div>
              )}
            </div>

            {/* Voice Audio Control Bar */}
            <div style={{
              marginTop: '12px',
              padding: '10px 14px',
              backgroundColor: 'var(--bg-surface-secondary)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '10px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <Headphones size={15} color="var(--primary)" />
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Voice Audio Mode:
                </span>
                <button
                  className={`icon-action-btn ${voiceMode === 'translated' ? 'selected' : ''}`}
                  onClick={() => {
                    setVoiceMode('translated');
                    if (videoRef.current && !videoRef.current.muted) videoRef.current.volume = 1.0;
                  }}
                  style={{
                    padding: '4px 10px',
                    fontSize: '11px',
                    fontWeight: 700,
                    backgroundColor: voiceMode === 'translated' ? 'var(--primary)' : 'transparent',
                    color: voiceMode === 'translated' ? '#FFFFFF' : 'var(--text-secondary)',
                  }}
                  title="Speaks translated sentences in target language while video plays"
                >
                  <Volume2 size={13} />
                  <span>Translated Voice ({LANG_NAMES[targetLang] || 'Target Language'})</span>
                </button>
                <button
                  className={`icon-action-btn ${voiceMode === 'original' ? 'selected' : ''}`}
                  onClick={() => {
                    setVoiceMode('original');
                    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
                    if (videoRef.current && !videoRef.current.muted) videoRef.current.volume = 1.0;
                  }}
                  style={{
                    padding: '4px 10px',
                    fontSize: '11px',
                    fontWeight: 600,
                    backgroundColor: voiceMode === 'original' ? 'var(--primary)' : 'transparent',
                    color: voiceMode === 'original' ? '#FFFFFF' : 'var(--text-secondary)',
                  }}
                  title="Hear original video audio at full volume"
                >
                  <span>Original Audio Only</span>
                </button>
              </div>

              {voiceMode === 'translated' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Voice Volume:</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={voiceVolume}
                    onChange={(e) => setVoiceVolume(parseFloat(e.target.value))}
                    style={{ width: '80px', accentColor: 'var(--primary)' }}
                  />
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {Math.round(voiceVolume * 100)}%
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Subtitle & Transcript Card */}
          <div className="glass-panel" style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', paddingBottom: '10px', borderBottom: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Dialogue Transcripts & Voice Playback
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: '8px' }}>
                  ({activeJob?.segments?.length || 0} segments)
                </span>
              </div>

              {/* Subtitle View Mode Switcher */}
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  className={`icon-action-btn ${subtitleMode === 'dual' ? 'selected' : ''}`}
                  onClick={() => setSubtitleMode('dual')}
                  style={{ padding: '4px 8px', fontSize: '11px' }}
                >
                  Dual
                </button>
                <button
                  className={`icon-action-btn ${subtitleMode === 'target' ? 'selected' : ''}`}
                  onClick={() => setSubtitleMode('target')}
                  style={{ padding: '4px 8px', fontSize: '11px' }}
                >
                  Target
                </button>
                <button
                  className={`icon-action-btn ${subtitleMode === 'source' ? 'selected' : ''}`}
                  onClick={() => setSubtitleMode('source')}
                  style={{ padding: '4px 8px', fontSize: '11px' }}
                >
                  Source
                </button>
              </div>
            </div>

            {/* Segments List with 1-Click Timestamp Seeking & Voice Playback */}
            {activeJob && activeJob.segments && activeJob.segments.length > 0 ? (
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '340px', paddingRight: '4px' }}>
                {activeJob.segments.map((seg, idx) => {
                  const isCurrent = activeSegmentIndex === idx;
                  return (
                    <div
                      key={`seg-${idx}`}
                      onClick={() => handleSeekToSegment(seg, idx)}
                      style={{
                        padding: '12px 14px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: isCurrent ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                        border: `1px solid ${isCurrent ? 'var(--primary-border)' : 'var(--border-color)'}`,
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                        <span style={{ fontWeight: 700, color: isCurrent ? 'var(--primary)' : 'var(--text-secondary)' }}>
                          #{seg.index || idx + 1}
                        </span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Clock size={11} />
                            <span>{seg.start_time || '00:00'} → {seg.end_time || '00:04'}</span>
                          </div>
                          <button
                            onClick={(e) => handlePlaySegmentVoice(seg, e)}
                            className="icon-action-btn"
                            style={{ padding: '3px 8px', fontSize: '11px', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '4px' }}
                            title="Listen to translated voice"
                          >
                            <Volume2 size={12} />
                            <span>Speak Voice</span>
                          </button>
                        </div>
                      </div>

                      {(subtitleMode === 'dual' || subtitleMode === 'source') && (
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '0 0 4px 0', lineHeight: 1.4 }}>
                          {seg.source_text}
                        </p>
                      )}

                      {(subtitleMode === 'dual' || subtitleMode === 'target') && (
                        <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary)', margin: 0, lineHeight: 1.4 }}>
                          {seg.target_text || seg.translated_text}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', minHeight: '180px' }}>
                <p style={{ fontSize: '13px' }}>
                  {isProcessing
                    ? `Translating video voice into ${LANG_NAMES[targetLang] || 'target language'}... Your video is running on screen above.`
                    : 'Upload any training video above to immediately view, play with sound, and translate speech into your chosen language.'}
                </p>
              </div>
            )}

            {/* Subtitle & Video Download Bar */}
            {activeJob && activeJob.status === 'COMPLETED' && (
              <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <a
                  href={`/api/video/download/${activeJob.job_id}/srt`}
                  target="_blank"
                  rel="noreferrer"
                  download
                  className="icon-action-btn"
                  style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Download size={14} />
                  <span>Download SRT</span>
                </a>
                <a
                  href={`/api/video/download/${activeJob.job_id}/vtt`}
                  target="_blank"
                  rel="noreferrer"
                  download
                  className="icon-action-btn"
                  style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Download size={14} />
                  <span>Download WebVTT</span>
                </a>
                <a
                  href={`/api/video/download/${activeJob.job_id}/mp4`}
                  target="_blank"
                  rel="noreferrer"
                  download
                  className="icon-action-btn"
                  style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Film size={14} />
                  <span>Download Dubbed Video (MP4)</span>
                </a>
                {activeJob.translated_audio_path && (
                  <a
                    href={`/api/video/audio/${activeJob.job_id}/translated`}
                    target="_blank"
                    rel="noreferrer"
                    download
                    className="icon-action-btn"
                    style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Music size={14} />
                    <span>Download Translated Voice (MP3)</span>
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
