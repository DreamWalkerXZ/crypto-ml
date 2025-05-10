import pandas as pd
import numpy as np
import talib
from typing import List, Tuple, Optional, Dict, Any
from logging import getLogger
import math

logger = getLogger(__name__)

class PreprocessingService:
    """Service for preprocessing financial data and calculating technical indicators"""

    def __init__(self):
        """Initialize the preprocessing service with supported technical indicators"""
        self.indicators_map = {
            'RSI': self._calculate_rsi,
            'MACD': self._calculate_macd,
            'SMA': self._calculate_sma,
            'EMA': self._calculate_ema,
            'BBANDS': self._calculate_bbands,
            'STOCH': self._calculate_stoch,
            'CCI': self._calculate_cci,
            'ADX': self._calculate_adx,
            'AO': self._calculate_ao,
            'MOM': self._calculate_mom,
            'STOCHRSI': self._calculate_stochrsi,
            'WILLR': self._calculate_willr,
            'BBP': self._calculate_bbp,
            'ULTOSC': self._calculate_ultosc,
            'VWMA': self._calculate_vwma,
            'HMA': self._calculate_hma,
            'ICHIMOKU_BASE': self._calculate_ichimoku_base,
            'WMA': self._calculate_wma,
        }

    def _parse_indicator_string(self, indicator_str: str) -> Tuple[str, List[Any]]:
        """
        Parse indicator string to get base name and parameters
        
        Args:
            indicator_str: Indicator string (e.g. 'SMA_20' or 'ULTOSC_7_14_28')
            
        Returns:
            Tuple containing base indicator name and list of parameters
        """
        parts = indicator_str.split('_')
        base_indicator = parts[0]
        params = []
        if len(parts) > 1:
            try:
                params = [int(p) for p in parts[1:]]
            except ValueError:
                logger.warning(f"Could not parse parameters for {indicator_str}, using defaults.")
                return base_indicator, []
        return base_indicator, params

    def _calculate_indicators(self, df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
        """
        Calculate specified technical indicators
        
        Args:
            df: Input DataFrame with OHLCV columns
            indicators: List of technical indicators to calculate
            
        Returns:
            DataFrame with added technical indicators
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Input DataFrame must contain columns: {required_cols}")

        df = df.copy()

        for indicator_str in indicators:
            base_indicator, params = self._parse_indicator_string(indicator_str)

            if base_indicator in self.indicators_map:
                try:
                    df = self.indicators_map[base_indicator](df, indicator_str, params)
                    logger.debug(f"Calculated indicator: {indicator_str}")
                except Exception as e:
                    logger.error(f"Failed to calculate indicator {indicator_str}: {e}", exc_info=True)
            else:
                logger.warning(f"Indicator '{base_indicator}' (from '{indicator_str}') is not supported.")
        return df

    def prepare_features_and_target(
        self,
        df: pd.DataFrame,
        ta_indicators: List[str],
        look_back: int,
        prediction_horizon: int,
        price_change_threshold: float = 0.002
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        """
        Prepare features and target variables for model training
        
        Args:
            df: DataFrame containing OHLCV data and timestamp
            ta_indicators: List of technical indicators to calculate
            look_back: Number of historical periods to use as features
            prediction_horizon: Number of periods ahead to predict target
            price_change_threshold: Relative threshold for determining positive price change
            
        Returns:
            Tuple containing feature matrix, target variable, and price data
        """
        if 'timestamp' not in df.columns:
             raise ValueError("Input DataFrame must contain a 'timestamp' column.")

        df_with_indicators = self._calculate_indicators(df, ta_indicators)
        X = self._create_features(df_with_indicators, look_back)
        y = self._create_target(df_with_indicators, prediction_horizon, price_change_threshold)

        combined = X.join(y.rename('target'), how='inner')
        combined = combined.dropna(subset=['target'])
        valid_indices = combined.index
        y = combined.loc[valid_indices, 'target'].astype(int)
        X = combined.drop(columns=['target'])
        price_data = df_with_indicators.loc[valid_indices].copy()

        X.index = price_data['timestamp']
        y.index = price_data['timestamp']
        price_data.index = price_data['timestamp']

        X.index.name = 'timestamp'
        y.index.name = 'timestamp'
        price_data.index.name = 'timestamp'

        original_len = len(X)
        X = X.dropna()
        y = y.loc[X.index]
        price_data = price_data.loc[X.index]
        if len(X) < original_len:
             logger.warning(f"Dropped {original_len - len(X)} rows from X due to NaNs introduced by indicators/lags.")

        if X.empty or y.empty:
             logger.error("Preprocessing resulted in empty features (X) or target (y). Check look_back, prediction_horizon, and data length.")

        return X, y, price_data

    def _create_features(self, df: pd.DataFrame, look_back: int) -> pd.DataFrame:
        """
        Create feature matrix using lagged OHLCV and current indicators
        
        Args:
            df: DataFrame with price data and technical indicators
            look_back: Number of historical periods for OHLCV lags
            
        Returns:
            Feature matrix DataFrame
        """
        features = []
        col_names = []

        price_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in price_cols:
            for i in range(look_back):
                shifted_col = df[col].shift(i)
                features.append(shifted_col)
                col_names.append(f'{col}_lag_{i}')

        indicator_cols = [col for col in df.columns if col not in ['timestamp'] + price_cols]
        for col in indicator_cols:
            features.append(df[col])
            col_names.append(col)

        X = pd.concat(features, axis=1)
        X.columns = col_names

        X = X.iloc[(look_back - 1):] if look_back > 0 else X

        return X

    def _create_target(self, df: pd.DataFrame, prediction_horizon: int, price_change_threshold: float) -> pd.Series:
        """
        Create target variable based on future price change
        
        Args:
            df: DataFrame with price data
            prediction_horizon: Number of periods ahead to predict
            price_change_threshold: Relative change threshold
            
        Returns:
            Target variable Series
        """
        if prediction_horizon <= 0:
            raise ValueError("prediction_horizon must be a positive integer.")

        future_close = df['close'].shift(-prediction_horizon)
        relative_change = (future_close - df['close']) / df['close']
        y = (relative_change > price_change_threshold).astype(float)
        y = y.where(future_close.notna(), np.nan)

        return y

    def _calculate_rsi(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate RSI indicator"""
        period = params[0] if params else 14
        col_name = f"RSI_{period}"
        df[col_name] = talib.RSI(df['close'], timeperiod=period)
        return df

    def _calculate_macd(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate MACD indicator"""
        fastperiod = params[0] if params else 12
        slowperiod = params[1] if len(params) > 1 else 26
        signalperiod = params[2] if len(params) > 2 else 9
        macd, signal, hist = talib.MACD(df['close'], fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        df['MACD'] = macd
        df['MACD_signal'] = signal
        df['MACD_hist'] = hist
        return df

    def _calculate_sma(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate SMA indicator"""
        period = params[0] if params else 30
        col_name = f"SMA_{period}"
        df[col_name] = talib.SMA(df['close'], timeperiod=period)
        return df

    def _calculate_ema(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate EMA indicator"""
        period = params[0] if params else 30
        col_name = f"EMA_{period}"
        df[col_name] = talib.EMA(df['close'], timeperiod=period)
        return df

    def _calculate_bbands(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Bollinger Bands indicator"""
        period = params[0] if params else 20
        nbdevup = params[1] if len(params) > 1 else 2
        nbdevdn = params[2] if len(params) > 2 else 2
        col_prefix = f"BB_{period}_{nbdevup}_{nbdevdn}"
        upper, middle, lower = talib.BBANDS(df['close'], timeperiod=period, nbdevup=nbdevup, nbdevdn=nbdevdn)
        df[f'{col_prefix}_upper'] = upper
        df[f'{col_prefix}_middle'] = middle
        df[f'{col_prefix}_lower'] = lower
        return df

    def _calculate_stoch(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Stochastic indicator"""
        fastk_period = params[0] if params else 14
        slowk_period = params[1] if len(params) > 1 else 3
        slowd_period = params[2] if len(params) > 2 else 3
        col_prefix = f"STOCH_{fastk_period}_{slowk_period}_{slowd_period}"
        slowk, slowd = talib.STOCH(df['high'], df['low'], df['close'],
                                   fastk_period=fastk_period,
                                   slowk_period=slowk_period,
                                   slowk_matype=0,
                                   slowd_period=slowd_period,
                                   slowd_matype=0)
        df[f'{col_prefix}_k'] = slowk
        df[f'{col_prefix}_d'] = slowd
        return df

    def _calculate_cci(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate CCI indicator"""
        period = params[0] if params else 20
        col_name = f"CCI_{period}"
        df[col_name] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=period)
        return df

    def _calculate_adx(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate ADX indicator"""
        period = params[0] if params else 14
        col_name = f"ADX_{period}"
        df[col_name] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=period)
        return df

    def _calculate_mom(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Momentum indicator"""
        period = params[0] if params else 10
        col_name = f"MOM_{period}"
        df[col_name] = talib.MOM(df['close'], timeperiod=period)
        return df

    def _calculate_stochrsi(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Stochastic RSI indicator"""
        timeperiod = params[0] if params else 14
        fastk_period = params[1] if len(params) > 1 else 14
        fastd_period = params[2] if len(params) > 2 else 3
        fastd_matype = params[3] if len(params) > 3 else 0

        col_prefix = f"STOCHRSI_{timeperiod}_{fastk_period}_{fastd_period}"
        fastk, fastd = talib.STOCHRSI(df['close'],
                                      timeperiod=timeperiod,
                                      fastk_period=fastk_period,
                                      fastd_period=fastd_period,
                                      fastd_matype=fastd_matype)
        df[f'{col_prefix}_k'] = fastk
        df[f'{col_prefix}_d'] = fastd
        return df

    def _calculate_willr(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Williams %R indicator"""
        period = params[0] if params else 14
        col_name = f"WILLR_{period}"
        df[col_name] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=period)
        return df

    def _calculate_ultosc(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Ultimate Oscillator indicator"""
        period1 = params[0] if params else 7
        period2 = params[1] if len(params) > 1 else 14
        period3 = params[2] if len(params) > 2 else 28
        col_name = f"ULTOSC_{period1}_{period2}_{period3}"
        df[col_name] = talib.ULTOSC(df['high'], df['low'], df['close'],
                                    timeperiod1=period1, timeperiod2=period2, timeperiod3=period3)
        return df

    def _calculate_ao(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Awesome Oscillator indicator"""
        median_price = (df['high'] + df['low']) / 2
        sma5 = talib.SMA(median_price, timeperiod=5)
        sma34 = talib.SMA(median_price, timeperiod=34)
        df['AO'] = sma5 - sma34
        return df

    def _calculate_bbp(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Bull Bear Power indicator"""
        period = params[0] if params else 13
        ema_close = talib.EMA(df['close'], timeperiod=period)
        df[f'BULLP_{period}'] = df['high'] - ema_close
        df[f'BEARP_{period}'] = df['low'] - ema_close
        return df

    def _calculate_vwma(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Volume Weighted Moving Average indicator"""
        period = params[0] if params else 20
        col_name = f"VWMA_{period}"
        vol_price_sum = (df['close'] * df['volume']).rolling(window=period, min_periods=period).sum()
        vol_sum = df['volume'].rolling(window=period, min_periods=period).sum()
        df[col_name] = vol_price_sum / vol_sum.replace(0, np.nan)
        return df

    def _calculate_wma(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Weighted Moving Average indicator"""
        if not params:
             raise ValueError("WMA requires a period parameter (e.g., WMA_10)")
        period = params[0]
        col_name = f"WMA_{period}"
        df[col_name] = talib.WMA(df['close'], timeperiod=period)
        return df

    def _calculate_hma(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Hull Moving Average indicator"""
        period = params[0] if params else 9
        col_name = f"HMA_{period}"

        period_half_int = int(period / 2)
        period_sqrt_int = int(math.sqrt(period))

        wma_half = talib.WMA(df['close'], timeperiod=period_half_int)
        wma_full = talib.WMA(df['close'], timeperiod=period)

        hma_step1 = 2 * wma_half - wma_full
        temp_series = pd.Series(hma_step1, index=df.index)
        df[col_name] = talib.WMA(temp_series.dropna(), timeperiod=period_sqrt_int)

        return df

    def _calculate_ichimoku_base(self, df: pd.DataFrame, indicator_str: str, params: List[int]) -> pd.DataFrame:
        """Calculate Ichimoku Base Line indicator"""
        period = params[0] if params else 26
        col_name = f"ICHIMOKU_BASE_{period}"
        high_max = df['high'].rolling(window=period, min_periods=period).max()
        low_min = df['low'].rolling(window=period, min_periods=period).min()
        df[col_name] = (high_max + low_min) / 2
        return df