export interface PageContext {
  route: string;
  page_name: string;
  selected_field_id?: number;
  selected_field_name?: string;
  selected_crop_id?: number;
  selected_crop_name?: string;
  selected_location?: {
    latitude: number;
    longitude: number;
    displayName: string;
  };
}

export interface AssistantToolCall {
  tool_name: string;
  status: 'pending' | 'running' | 'success' | 'error';
  arguments?: Record<string, any>;
  result?: any;
  label?: string;
  summary?: string;
}

export interface AssistantAction {
  type: 'navigate' | 'open_field' | 'open_crop' | 'open_weather' | 'open_market' | 'open_camera';
  route: string;
  label: string;
  params?: Record<string, any>;
}

export interface AssistantCardDataPoint {
  label: string;
  value: string;
}

export interface AssistantCard {
  type: 'weather' | 'irrigation' | 'market' | 'disease' | 'brief' | 'crop' | 'generic';
  title: string;
  subtitle?: string;
  description?: string;
  metric?: string;
  data_points?: AssistantCardDataPoint[];
  action_route?: string;
  action_label?: string;
}

export interface AssistantMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tool_calls?: AssistantToolCall[];
  actions?: AssistantAction[];
  card?: AssistantCard;
  sources?: string[];
  tool_summary?: string[];
  metadata?: Record<string, any>;
  created_at: string;
  isStreaming?: boolean;
}

export interface ConversationSummary {
  id: string;
  title: string;
  active_field_id?: number;
  active_crop_id?: number;
  page_context?: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  last_message_at: string;
}
