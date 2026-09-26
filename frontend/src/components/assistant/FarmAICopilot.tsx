import React from 'react';
import { AssistantLauncher } from './AssistantLauncher';
import { AssistantPanel } from './AssistantPanel';

export const FarmAICopilot: React.FC = () => {
  return (
    <>
      <AssistantLauncher />
      <AssistantPanel />
    </>
  );
};
