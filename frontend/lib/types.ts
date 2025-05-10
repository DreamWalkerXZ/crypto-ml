export interface AvailableDataResponse {
  symbol: string;
  timeframe: string;
  start_timestamp: string;
  end_timestamp: string;
  data_points: number;
}

export interface DataFetchRequest {
  symbol: string;
  timeframe: string;
  start_timestamp: string;
  end_timestamp: string;
}

export interface BacktestParams {
  symbol: string;
  timeframe: string;
  start_timestamp: string;
  end_timestamp: string;
  ta_indicators: string[];
  look_back: number;
  prediction_horizon: number;
  price_change_threshold: number;
  model_name: string;
  model_params: Record<string, any> | null;
  retrain_interval: number;
  window_size: number;
  buy_threshold: number;
  sell_threshold: number;
  stop_loss_pct: number;
  initial_balance: number;
  transaction_fee: number;
  max_position_size?: number | null;
  min_position_size?: number | null;
  risk_free_rate?: number;
  slippage?: number;
}

export interface ModelInfo {
  name: string;
  description: string;
  parameters: Record<string, any>;
  required_features: string[];
  requires_input_size: boolean;
  default_params: Record<string, any>;
}

export interface ResponseModel<T> {
  success: boolean;
  data: T | null;
  message?: string;
}

export interface BacktestResult {
  id: string;
  params: {
    symbol: string;
    timeframe: string;
    model_name: string;
    model_params: Record<string, any> | null;
    look_back: number;
    prediction_horizon: number;
    retrain_interval: number;
    window_size: number;
    buy_threshold: number;
    sell_threshold: number;
    stop_loss_pct: number;
    initial_balance: number;
    transaction_fee: number;
    start_timestamp: string;
    end_timestamp: string;
    ta_indicators: string[];
    slippage: number;
    risk_free_rate: number;
  };
  results: {
    total_return_pct: number;
    annualized_return_pct: number;
    max_drawdown_pct: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    calmar_ratio: number;
    win_rate_pct: number;
    profit_factor: number;
    total_trades: number;
    max_drawdown_duration: number;
    volatility_pct: number;
    consecutive_losses: number;
    avg_trade_return_pct: number;
    avg_winning_trade_pct: number;
    avg_losing_trade_pct: number;
    avg_holding_period: number;
    max_holding_period: number;
    min_holding_period: number;
    total_fees: number;
    equity_curve: Array<{
      time: string;
      value: number;
    }>;
    trade_logs: Array<{
      timestamp: string;
      type: 'buy' | 'sell';
      price: number;
      shares: number;
      fee_cash: number;
      reason?: string;
    }>;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
}

export interface BacktestListItem {
  id: string;
  symbol: string;
  timeframe: string;
  model_name: string;
  start_timestamp: string;
  end_timestamp: string;
  total_return_pct: number;
  annualized_return_pct: number;
  sharpe_ratio: number;
  win_rate_pct: number;
  created_at: string;
} 