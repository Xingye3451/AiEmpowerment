declare global {
  namespace AIConfig {
    export interface AIService {
      id: number;
      service_type: string;
      service_name: string;
      service_url: string;
      is_active: boolean;
      is_default: boolean;
      priority: number;
      timeout: number;
      advanced_params?: any;
      auto_detect?: boolean;
      language?: string;
      quality?: string;
      model_type?: string;
      batch_size?: number;
      smooth?: boolean;
      created_at: string;
      updated_at: string;
    }
    
    export interface SystemConfig {
      id: number;
      queue_size: number;
      upload_dir: string;
      result_dir: string;
      temp_dir: string;
      auto_clean: boolean;
      retention_days: number;
      notify_completion: boolean;
      notify_error: boolean;
      log_level: string;
      created_at: string;
      updated_at: string;
    }
    
    export interface ServiceStats {
      service_id: number;
      service_name: string;
      service_type: string;
      is_active: boolean;
      is_default: boolean;
      total_calls: number;
      success_rate: number;
      avg_response_time: number;
      daily_stats: Record<string, any>;
      last_check: string;
    }
    
    export interface TestConnectionResult {
      success: boolean;
      message: string;
      details?: any;
    }
  }
}

export function fetchAIServices(serviceType?: string): Promise<AIConfig.AIService[]>;
export function fetchAIService(serviceId: number): Promise<AIConfig.AIService>;
export function createAIService(serviceData: any): Promise<AIConfig.AIService>;
export function updateAIService(serviceId: number, serviceData: any): Promise<AIConfig.AIService>;
export function deleteAIService(serviceId: number): Promise<any>;
export function fetchSystemConfig(): Promise<AIConfig.SystemConfig>;
export function updateSystemConfig(configData: any): Promise<AIConfig.SystemConfig>;
export function testServiceConnection(testData: { service_type: string; service_url: string }): Promise<AIConfig.TestConnectionResult>;

export {}; 