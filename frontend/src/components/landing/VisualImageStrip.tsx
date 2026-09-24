import React from 'react';

interface StripItem {
  id: string;
  title: string;
  image: string;
  category: string;
}

const STRIP_ITEMS: StripItem[] = [
  { id: '1', title: 'Crop Intelligence', image: '/images/crop-intelligence.webp', category: 'Wheat & Rice' },
  { id: '2', title: 'Plant Health', image: '/images/plant-health.webp', category: 'Diagnostics' },
  { id: '3', title: 'Pest Risk', image: '/images/pest-intelligence.webp', category: 'Insect Control' },
  { id: '4', title: 'Subsurface Soil', image: '/images/soil-intelligence.webp', category: 'Topsoil Carbon' },
  { id: '5', title: 'Irrigation', image: '/images/irrigation.webp', category: 'Water Dynamics' },
  { id: '6', title: 'Harvest Yield', image: '/images/yield-intelligence.webp', category: 'Combines' },
  { id: '7', title: 'Smart Farming', image: '/images/smart-farming.webp', category: 'Drone Inspection' },
];

export const VisualImageStrip: React.FC = () => {
  return (
    <section className="py-16 bg-[#FAFBF7] overflow-hidden border-b border-[#E2E7DA]">
      <div className="max-w-7xl mx-auto px-6 sm:px-12">
        <div className="text-center mb-10 space-y-2">
          <span className="text-[11px] font-extrabold uppercase tracking-widest text-[#2F6B3C]">
            Visual Agricultural Spectrum
          </span>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0B1C10]">
            Every Layer of the Field Covered
          </h3>
        </div>

        {/* Circular / Organic Overlapping Image Strip */}
        <div className="flex items-center justify-start lg:justify-center gap-2 sm:gap-4 md:-space-x-6 overflow-x-auto pb-6 scrollbar-none snap-x">
          {STRIP_ITEMS.map((item, idx) => (
            <div
              key={item.id}
              className="relative shrink-0 snap-center group cursor-pointer transition-all duration-500 transform hover:scale-110 hover:z-30 hover:-translate-y-2"
              style={{ transitionDelay: `${idx * 50}ms` }}
            >
              {/* Circular Organic Image Frame */}
              <div className="w-36 h-36 sm:w-48 sm:h-48 rounded-full overflow-hidden p-1.5 bg-white border-2 border-[#D6E4CC] shadow-xl group-hover:border-[#D4E768] group-hover:shadow-2xl transition-all">
                <img
                  src={item.image}
                  alt={item.title}
                  className="w-full h-full object-cover rounded-full transition-transform duration-700 group-hover:scale-110"
                />
              </div>

              {/* Hover Badge Label */}
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none z-40 whitespace-nowrap">
                <div className="px-3 py-1 rounded-full bg-[#0B1C10] text-[#D4E768] text-[10px] font-bold uppercase tracking-wider shadow-lg border border-[#D4E768]/30">
                  {item.title}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
