import { BacktestParams, DataFetchRequest, BacktestResult, ApiResponse, BacktestListItem } from '@/lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

// Data related APIs
export const fetchData = async (params: DataFetchRequest) => {
  try {
    const response = await fetch(`${API_BASE_URL}/data/fetch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data,
      message: result.message
    };
  } catch (error) {
    console.error('Failed to fetch data:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to fetch data'
    };
  }
};

export const getAvailableData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/data/available`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data || [],
      message: result.message
    };
  } catch (error) {
    console.error('Failed to get available data:', error);
    return {
      success: false,
      data: [],
      message: error instanceof Error ? error.message : 'Failed to fetch data'
    };
  }
};

export const getOhlcvData = async (
  symbol: string,
  timeframe: string,
  startTimestamp: string,
  endTimestamp: string
) => {
  try {
    const url = new URL(`${API_BASE_URL}/data/ohlcv`);
    url.searchParams.append("symbol", symbol);
    url.searchParams.append("timeframe", timeframe);
    url.searchParams.append("start_timestamp", startTimestamp);
    url.searchParams.append("end_timestamp", endTimestamp);

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data,
      message: result.message
    };
  } catch (error) {
    console.error('Failed to fetch OHLCV data:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to fetch OHLCV data'
    };
  }
};

// Backtest related APIs
export const runBacktest = async (params: BacktestParams) => {
  try {
    const response = await fetch(`${API_BASE_URL}/backtest/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data,
      message: result.message
    };
  } catch (error) {
    console.error('Failed to run backtest:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to run backtest'
    };
  }
};

export const getBacktestStatus = async (taskId: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/backtest/tasks/${taskId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data,
      message: result.message
    };
  } catch (error) {
    console.error('Failed to get backtest status:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to get backtest status'
    };
  }
};

export const listTasks = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/backtest/tasks`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data || [],
      message: result.message
    };
  } catch (error) {
    console.error('Failed to get task list:', error);
    return {
      success: false,
      data: [],
      message: error instanceof Error ? error.message : 'Failed to get task list'
    };
  }
};

export async function getBacktestResult(id: string): Promise<ApiResponse<BacktestResult>> {
  try {
    const response = await fetch(`${API_BASE_URL}/backtest/results/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data,
      message: result.message
    };
  } catch (error) {
    console.error('Error fetching backtest results:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to fetch backtest results',
    };
  }
}

export const listBacktestResults = async (): Promise<ApiResponse<BacktestListItem[]>> => {
  try {
    const response = await fetch(`${API_BASE_URL}/backtest/results`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data || [],
      message: result.message
    };
  } catch (error) {
    console.error('Failed to get backtest results list:', error);
    return {
      success: false,
      data: [],
      message: error instanceof Error ? error.message : 'Failed to get backtest results list'
    };
  }
};

// Model related APIs
export const getAvailableModels = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/models`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data || [],
      message: result.message
    };
  } catch (error) {
    console.error('Failed to get available models:', error);
    return {
      success: false,
      data: [],
      message: error instanceof Error ? error.message : 'Failed to get available models'
    };
  }
};

export const getModelInfo = async (modelName: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/models/${modelName}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return {
      success: true,
      data: result.data,
      message: result.message
    };
  } catch (error) {
    console.error('Failed to get model information:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to get model information'
    };
  }
}; 