import React from 'react';
import { HourlyForecastItem } from '../../types/api';
import { getWeatherCodeDetails } from '../../utils/weatherCodeMapper';

interface WeatherHourlyTimelineProps {
  hourly: HourlyForecastItem[];
  selectedTime: string | null;
  onSelectHour: (item: HourlyForecastItem) => void;
}

export const WeatherHourlyTimeline: React.FC<WeatherHourlyTimelineProps> = ({
  hourly,
  selectedTime,
  onSelectHour,
}) => {
  if (!hourly || hourly.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs px-1">
        <span className="font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
          <span>●</span> 24-HOUR INTERACTIVE FORECAST SCENE TIMELINE
        </span>
        <span className="text-[11px] text-[#D4E768]">
          Click any hour to preview atmospheric scene
        </span>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-3 pt-1 scrollbar-thin scrollbar-thumb-white/20">
        {hourly.slice(0, 24).map((item, idx) => {
          const timeLabel = new Date(item.time).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          });
          const isDay = item.is_day !== undefined ? Boolean(item.is_day) : true;
          const details = getWeatherCodeDetails(item.weather_code, isDay);
          const isSelected = selectedTime === item.time || (idx === 0 && !selectedTime);

          return (
            <button
              key={idx}
              onClick={() => onSelectHour(item)}
              className={`shrink-0 w-28 p-3 rounded-2xl border text-left transition-all duration-300 backdrop-blur-md ${
                isSelected
                  ? 'bg-[#D4E768] text-[#0B1C10] border-[#D4E768] scale-105 shadow-lg font-bold'
                  : 'bg-black/30 text-white border-white/10 hover:bg-black/50 hover:border-white/20'
              }`}
            >
              <span className="text-[10px] font-mono block opacity-80 uppercase tracking-wider">
                {idx === 0 ? 'NOW' : timeLabel}
              </span>

              <div className="my-2">
                <span className="text-xl font-black font-editorial block">
                  {item.temperature.toFixed(1)}°
                </span>
                <span
                  className={`text-[11px] font-semibold block truncate ${
                    isSelected ? 'text-[#0B1C10]' : 'text-slate-300'
                  }`}
                >
                  {details.label}
                </span>
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono border-t pt-1.5 border-current/20">
                <span>💧 {item.relative_humidity}%</span>
                <span>🌧️ {item.precipitation}mm</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
