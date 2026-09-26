import React from 'react';
import { Sparkles, CalendarCheck, Droplets, Sun, TrendingUp, ShieldAlert, Sprout, Leaf } from 'lucide-react';
import { useFarmAICopilot } from '../../context/FarmAICopilotContext';

interface QuickActionItem {
  label: string;
  query: string;
  icon?: React.ReactNode;
}

export const AssistantQuickActions: React.FC = () => {
  const { pageContext, sendMessage, isStreaming } = useFarmAICopilot();

  const route = pageContext.route;

  let actions: QuickActionItem[] = [];

  if (route.includes('weather')) {
    actions = [
      { label: 'Weather impact', query: 'How will today weather affect my active crops?', icon: <Sun className="w-3.5 h-3.5 text-amber-400" /> },
      { label: 'Should I irrigate?', query: 'Based on current weather, should I irrigate today?', icon: <Droplets className="w-3.5 h-3.5 text-cyan-400" /> },
      { label: 'Rain forecast', query: 'What is the 7-day rainfall outlook for my farm location?', icon: <Sun className="w-3.5 h-3.5 text-blue-400" /> },
      { label: 'What to watch', query: 'What weather risks should I watch out for today?', icon: <ShieldAlert className="w-3.5 h-3.5 text-rose-400" /> },
    ];
  } else if (route.includes('irrigation')) {
    actions = [
      { label: 'Irrigate today?', query: 'Should I water my field today based on soil moisture and forecast?', icon: <Droplets className="w-3.5 h-3.5 text-cyan-400" /> },
      { label: 'Rain effect on water', query: 'Will predicted rain reduce my irrigation requirement?', icon: <Droplets className="w-3.5 h-3.5 text-blue-400" /> },
      { label: 'Explain SWC model', query: 'Explain the 3-hour soil water content prediction for my field.', icon: <Sparkles className="w-3.5 h-3.5 text-emerald-400" /> },
    ];
  } else if (route.includes('market')) {
    actions = [
      { label: 'Crop price trend', query: 'What is happening to my crop prices in the market right now?', icon: <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> },
      { label: '30-day forecast', query: 'What is the 30-day market price trend for my main crop?', icon: <TrendingUp className="w-3.5 h-3.5 text-teal-400" /> },
      { label: 'Price signals', query: 'Are market conditions favorable for selling currently?', icon: <Sparkles className="w-3.5 h-3.5 text-amber-400" /> },
    ];
  } else if (route.includes('crop')) {
    actions = [
      { label: 'Recommend a crop', query: 'What crop is best suited for my field conditions?', icon: <Sprout className="w-3.5 h-3.5 text-emerald-400" /> },
      { label: 'Why recommend this?', query: 'Why is this crop recommended for my soil and climate?', icon: <Sparkles className="w-3.5 h-3.5 text-lime-400" /> },
      { label: 'Sowing suitability', query: 'Is the current window suitable for sowing?', icon: <CalendarCheck className="w-3.5 h-3.5 text-cyan-400" /> },
    ];
  } else if (route.includes('disease') || route.includes('pest')) {
    actions = [
      { label: 'Disease guidance', query: 'What plant disease signs should I check on my crops?', icon: <Leaf className="w-3.5 h-3.5 text-emerald-400" /> },
      { label: 'Environmental pest risk', query: 'What is the current environmental pest risk in my area?', icon: <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> },
    ];
  } else {
    // Default / Dashboard
    actions = [
      { label: 'What should I do today?', query: 'What should I do today on my farm?', icon: <CalendarCheck className="w-3.5 h-3.5 text-emerald-400" /> },
      { label: 'Should I irrigate?', query: 'Should I irrigate my crops today?', icon: <Droplets className="w-3.5 h-3.5 text-cyan-400" /> },
      { label: 'Weather impact', query: 'How will today weather affect my crops?', icon: <Sun className="w-3.5 h-3.5 text-amber-400" /> },
      { label: 'Market update', query: 'What is the latest market trend for my crops?', icon: <TrendingUp className="w-3.5 h-3.5 text-teal-400" /> },
      { label: 'Farm health summary', query: 'Give me a summary of my farm status and active crops.', icon: <Sprout className="w-3.5 h-3.5 text-lime-400" /> },
    ];
  }

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto py-2 px-3 no-scrollbar border-b border-emerald-500/10 bg-emerald-950/30">
      {actions.map((act, index) => (
        <button
          key={index}
          disabled={isStreaming}
          onClick={() => sendMessage(act.query)}
          className="inline-flex items-center gap-1.5 shrink-0 px-3 py-1.5 rounded-full bg-emerald-900/40 hover:bg-emerald-800/60 border border-emerald-500/20 hover:border-emerald-400/40 text-[12px] font-medium text-emerald-100 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {act.icon}
          <span>{act.label}</span>
        </button>
      ))}
    </div>
  );
};
