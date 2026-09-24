import React from 'react';
import { Navbar } from '../components/landing/Navbar';
import { HeroSection } from '../components/landing/HeroSection';
import { IntroSection } from '../components/landing/IntroSection';
import { VisualImageStrip } from '../components/landing/VisualImageStrip';
import { SmartFarmingSection } from '../components/landing/SmartFarmingSection';
import { EcosystemGrid } from '../components/landing/EcosystemGrid';
import { CropSection } from '../components/landing/CropSection';
import { PlantHealthSection } from '../components/landing/PlantHealthSection';
import { LiveVisionSection } from '../components/landing/LiveVisionSection';
import { SoilWaterSection } from '../components/landing/SoilWaterSection';
import { PestSection } from '../components/landing/PestSection';
import { YieldSection } from '../components/landing/YieldSection';
import { WeatherMarketSection } from '../components/landing/WeatherMarketSection';
import { SmartFarmingValues } from '../components/landing/SmartFarmingValues';
import { CropTimeline } from '../components/landing/CropTimeline';
import { HowItWorks } from '../components/landing/HowItWorks';
import { TransparencySection } from '../components/landing/TransparencySection';
import { FinalCTA } from '../components/landing/FinalCTA';
import { LandingFooter } from '../components/landing/LandingFooter';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#FAFBF7] text-[#0B1C10] font-sans selection:bg-[#D4E768] selection:text-[#0B1C10]">
      {/* 1. Translucent Floating Navigation Capsule */}
      <Navbar />

      {/* 2. VerdaAgro-Level Cinematic Editorial Hero Section */}
      <HeroSection />

      {/* 3. Section 2: Large Editorial Intro Statement */}
      <IntroSection />

      {/* 4. Section 3: Organic Circular Overlapping Agricultural Image Strip */}
      <VisualImageStrip />

      {/* 5. Section 4: Smart Agriculture Framework */}
      <SmartFarmingSection />

      {/* 6. Section 5: Asymmetric Core AI Feature Ecosystem */}
      <EcosystemGrid />

      {/* 7. Section 6: Crop Recommendation & Soil Matching */}
      <CropSection />

      {/* 8. Section 7: Plant Disease Diagnostics & Grad-CAM Heatmap */}
      <PlantHealthSection />

      {/* 9. Section 8: Live AI Camera Real-Time Computer Vision */}
      <LiveVisionSection />

      {/* 10. Section 9: Soil Carbon & 3-Hour Water Forecast */}
      <SoilWaterSection />

      {/* 11. Section 10: Pest Species & Outbreak Risk */}
      <PestSection />

      {/* 12. Section 11: Yield Prediction & Uncertainty Bounds */}
      <YieldSection />

      {/* 13. Section 12: Weather Telemetry & Mandi Market Signals */}
      <WeatherMarketSection />

      {/* 14. Section 13: Three Core Smart Farming Values (01 Data-Driven, 02 Field-Aware, 03 Transparent) */}
      <SmartFarmingValues />

      {/* 15. Section 14: Seasonal Crop Timeline */}
      <CropTimeline />

      {/* 16. Section 15: 4-Step Analytical Workflow */}
      <HowItWorks />

      {/* 17. Section 16: Model Transparency & Limitations Breakdown */}
      <TransparencySection />

      {/* 18. Section 17: Final Full-Width Visual Call to Action */}
      <FinalCTA />

      {/* 19. Multi-Column Premium Dark Green Footer */}
      <LandingFooter />
    </div>
  );
};
