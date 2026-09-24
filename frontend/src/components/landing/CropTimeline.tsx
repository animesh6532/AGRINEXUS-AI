import React from 'react';
import { Link } from 'react-router-dom';
import { Calendar, ArrowRight } from 'lucide-react';

interface Stage {
  num: string;
  title: string;
  desc: string;
  image: string;
}

export const CropTimeline: React.FC = () => {
  const stages: Stage[] = [
    {
      num: '01',
      title: 'Sowing',
      desc: 'Optimal seed variety selection & soil N-P-K nutrient matching.',
      image: '/images/crop-calendar.webp'
    },
    {
      num: '02',
      title: 'Growth',
      desc: 'Canopy inspection & vegetative health monitoring.',
      image: '/images/crop-intelligence.webp'
    },
    {
      num: '03',
      title: 'Protection',
      desc: 'Disease visual heatmaps & pest species classification.',
      image: '/images/plant-health.webp'
    },
    {
      num: '04',
      title: 'Irrigation',
      desc: '3-hour Soil Water Content forecast & wilting point alerts.',
      image: '/images/irrigation.webp'
    },
    {
      num: '05',
      title: 'Harvest',
      desc: 'XGBoost yield forecast & Mandi market sale timing.',
      image: '/images/yield-intelligence.webp'
    }
  ];

  return (
    <section className="py-24 lg:py-32 px-6 sm:px-12 bg-[#FAFBF7] border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto space-y-16 text-left">
        
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div className="space-y-3">
            <span className="text-xs font-extrabold uppercase tracking-widest text-[#2F6B3C]">
              Agronomic Season Progression
            </span>
            <h2 className="editorial-heading text-[#0B1C10]">
              Seasonal Crop Timeline
            </h2>
          </div>

          <Link
            to="/crop-calendar"
            className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#2F6B3C] hover:underline"
          >
            <span>Explore Full Crop Calendar</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Editorial Horizontal Timeline Grid with Thin Line & Small Crop Images */}
        <div className="relative pt-6">
          
          {/* Thin Horizontal Connecting Line (Desktop) */}
          <div className="hidden lg:block absolute top-20 left-12 right-12 h-0.5 bg-[#E2E7DA] -z-0" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 relative z-10">
            {stages.map((stage, idx) => (
              <div
                key={idx}
                className="agri-card p-6 flex flex-col justify-between space-y-6 hover:border-[#2F6B3C] transition-all group"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-black font-sans text-[#2F6B3C]">
                      {stage.num}
                    </span>
                    <div className="w-12 h-12 rounded-full overflow-hidden border border-[#E2E7DA] group-hover:border-[#2F6B3C] transition-colors">
                      <img
                        src={stage.image}
                        alt={stage.title}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-lg font-extrabold text-[#0B1C10] group-hover:text-[#2F6B3C] transition-colors">
                      {stage.title}
                    </h3>
                    <p className="text-xs text-[#39463B] leading-relaxed">
                      {stage.desc}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

        </div>

      </div>
    </section>
  );
};
