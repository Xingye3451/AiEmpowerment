import React from 'react';

export interface SystemConfigPanelProps {
  systemConfig: AIConfig.SystemConfig;
  onSystemConfigUpdate: (config: AIConfig.SystemConfig) => void;
}

declare const SystemConfigPanel: React.FC<SystemConfigPanelProps>;
export default SystemConfigPanel; 