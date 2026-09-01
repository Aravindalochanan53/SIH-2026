import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { PrivateRoute } from './components/PrivateRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { HomePage } from './pages/HomePage';
import { VoiceTranslatorPage } from './pages/VoiceTranslatorPage';
import { VideoTranslatorPage } from './pages/VideoTranslatorPage';
import { ChatbotPage } from './pages/ChatbotPage';
import { LiveMeetingPage } from './pages/LiveMeetingPage';
import { LearningPage } from './pages/LearningPage';
import { WorksheetsPage } from './pages/WorksheetsPage';
import { OfflinePage } from './pages/OfflinePage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { ProfilePage } from './pages/ProfilePage';
import { useAppStore } from './store/useAppStore';
import { getCapabilities } from './api';

function AppShell({ children }) {
  return (
    <div className="app-layout-shell">
      <Sidebar />
      <div className="main-content-wrapper">
        <Navbar />
        <main className="page-content-area">{children}</main>
      </div>
    </div>
  );
}

export default function App() {
  const { setCapabilities, isAuthenticated } = useAppStore();

  useEffect(() => {
    if (isAuthenticated) {
      getCapabilities()
        .then(setCapabilities)
        .catch((e) => console.log('Capabilities load notice:', e));
    }
  }, [setCapabilities, isAuthenticated]);

  return (
    <Routes>
      {/* Public Auth Routes */}
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
      } />
      <Route path="/register" element={
        isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />
      } />

      {/* Protected App Routes */}
      <Route path="/" element={
        <PrivateRoute>
          <AppShell><DashboardPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/translate" element={
        <PrivateRoute>
          <AppShell><HomePage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/voice" element={
        <PrivateRoute>
          <AppShell><VoiceTranslatorPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/video" element={
        <PrivateRoute>
          <AppShell><VideoTranslatorPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/chat" element={
        <PrivateRoute>
          <AppShell><ChatbotPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/meeting" element={
        <PrivateRoute>
          <AppShell><LiveMeetingPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/learning" element={
        <PrivateRoute>
          <AppShell><LearningPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/worksheets" element={
        <PrivateRoute>
          <AppShell><WorksheetsPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/offline" element={
        <PrivateRoute>
          <AppShell><OfflinePage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/history" element={
        <PrivateRoute>
          <AppShell><HistoryPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/settings" element={
        <PrivateRoute>
          <AppShell><SettingsPage /></AppShell>
        </PrivateRoute>
      } />
      <Route path="/profile" element={
        <PrivateRoute>
          <AppShell><ProfilePage /></AppShell>
        </PrivateRoute>
      } />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
