declare namespace AIConfig {
  interface AIService {
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
  
  interface SystemConfig {
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
  
  interface ServiceStats {
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
  
  interface TestConnectionResult {
    success: boolean;
    message: string;
    details?: any;
  }
} 