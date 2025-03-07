import React from 'react';

export interface ServiceConfigPanelProps {
  services: AIConfig.AIService[];
  onServicesUpdate: (services: AIConfig.AIService[]) => void;
}

declare const ServiceConfigPanel: React.FC<ServiceConfigPanelProps>;
export default ServiceConfigPanel; 