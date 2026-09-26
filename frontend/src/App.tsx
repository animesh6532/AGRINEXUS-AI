import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { HealthProvider } from './context/HealthContext';
import { LocationProvider } from './context/LocationContext';
import { FarmerProfileProvider } from './context/FarmerProfileContext';
import { AppShell } from './components/layout/AppShell';

import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';

import { Dashboard } from './pages/Dashboard';
import { CropPage } from './pages/CropPage';
import { DiseasePage } from './pages/DiseasePage';
import { PestPage } from './pages/PestPage';
import { FertilizerPage } from './pages/FertilizerPage';
import { IrrigationPage } from './pages/IrrigationPage';
import { SoilPage } from './pages/SoilPage';
import { YieldPage } from './pages/YieldPage';
import { LiveCameraPage } from './pages/LiveCameraPage';
import { WeatherPage } from './pages/WeatherPage';
import { MarketPage } from './pages/MarketPage';
import { CropCalendarPage } from './pages/CropCalendarPage';
import { HistoryPage } from './pages/HistoryPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsPage } from './pages/SettingsPage';

import { FarmAICopilotProvider } from './context/FarmAICopilotContext';
import { FarmAICopilot } from './components/assistant/FarmAICopilot';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <HealthProvider>
        <LocationProvider>
          <FarmerProfileProvider>
            <BrowserRouter>
              <FarmAICopilotProvider>
                <Routes>
                  {/* Public Routes */}
                  <Route path="/" element={<LandingPage />} />
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/signup" element={<SignupPage />} />
                  <Route path="/forgot-password" element={<ForgotPasswordPage />} />

                  {/* Protected Platform Routes */}
                  <Route
                    element={
                      <ProtectedRoute>
                        <AppShell />
                      </ProtectedRoute>
                    }
                  >
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/crop" element={<CropPage />} />
                    <Route path="/disease" element={<DiseasePage />} />
                    <Route path="/pest" element={<PestPage />} />
                    <Route path="/fertilizer" element={<FertilizerPage />} />
                    <Route path="/irrigation" element={<IrrigationPage />} />
                    <Route path="/soil" element={<SoilPage />} />
                    <Route path="/yield" element={<YieldPage />} />
                    <Route path="/live" element={<LiveCameraPage />} />
                    <Route path="/weather" element={<WeatherPage />} />
                    <Route path="/market" element={<MarketPage />} />
                    <Route path="/crop-calendar" element={<CropCalendarPage />} />
                    <Route path="/history" element={<HistoryPage />} />
                    <Route path="/profile" element={<ProfilePage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                  </Route>

                  {/* Catch-all fallback */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
                <FarmAICopilot />
              </FarmAICopilotProvider>
            </BrowserRouter>
          </FarmerProfileProvider>
        </LocationProvider>
      </HealthProvider>
    </AuthProvider>
  );
};

export default App;

