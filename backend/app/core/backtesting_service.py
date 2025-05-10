from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
from datetime import datetime
from app.schemas.backtest import (
    BacktestParams,
    TradeLog,
    BacktestMetrics,
    BacktestResult,
    EquityPoint,
)
from app.core.modeling_service import BaseClassifierModel
import logging
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestingService:
    """Service for executing backtesting and calculating performance metrics"""
    
    def __init__(self):
        """Initialize the backtesting service"""
        pass

    def _calculate_annual_periods(self, timeframe: str) -> float:
        """
        Calculate annualized periods based on timeframe
        
        Args:
            timeframe: Timeframe string (e.g., '1h', '4h', '15m')
            
        Returns:
            float: Number of periods in a year
        """
        # Parse time unit
        unit = timeframe[-1].lower()
        value = int(timeframe[:-1])

        # Calculate minutes per period
        if unit == "m":
            minutes_per_period = value
        elif unit == "h":
            minutes_per_period = value * 60
        elif unit == "d":
            minutes_per_period = value * 1440
        else:
            raise ValueError(f"Unknown time unit: {unit}")

        # Calculate annual periods (365 days * 24 hours * 60 minutes / minutes per period)
        return (365 * 24 * 60) / minutes_per_period

    def _validate_input_data(
        self, X: pd.DataFrame, y: pd.Series, price_data: pd.DataFrame
    ) -> None:
        """
        Validate input data for backtesting
        
        Args:
            X: Feature data
            y: Target variable
            price_data: Price data
            
        Raises:
            ValueError: If data validation fails
        """
        # Check data length consistency
        if len(X) != len(y) or len(X) != len(price_data):
            raise ValueError("Feature data, target variable and price data lengths do not match")

        # Check index consistency
        if not (X.index.equals(y.index) and X.index.equals(price_data.index)):
            raise ValueError("Feature data, target variable and price data indices do not match")

        # Check required price columns
        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [
            col for col in required_columns if col not in price_data.columns
        ]
        if missing_columns:
            raise ValueError(f"Price data missing required columns: {missing_columns}")

        # Check for missing values
        if (
            X.isnull().any().any()
            or y.isnull().any()
            or price_data.isnull().any().any()
        ):
            raise ValueError("Data contains missing values")

        # Check if price data is time-sorted
        if not price_data.index.is_monotonic_increasing:
            raise ValueError("Price data is not time-sorted")

    def _execute_trade(
        self,
        current_time: datetime,
        current_price: float,
        position: int,
        shares: float,
        cash: float,
        pred_prob: float,
        params: BacktestParams,
        last_trade: Optional[TradeLog] = None,
    ) -> Tuple[int, float, float, Optional[TradeLog]]:
        """
        Execute trading logic based on current conditions
        
        Args:
            current_time: Current timestamp
            current_price: Current price
            position: Current position (0: no position, 1: long)
            shares: Current number of shares
            cash: Current cash balance
            pred_prob: Model prediction probability
            params: Backtest parameters
            last_trade: Last trade log
            
        Returns:
            Tuple containing:
                - New position
                - New shares
                - New cash balance
                - New trade log (if any)
        """
        new_trade = None
        
        # Check if price is valid
        if current_price <= 0:
            return position, shares, cash, None

        # Apply slippage
        effective_price = (
            current_price * (1 + params.slippage)
            if position == 0
            else current_price * (1 - params.slippage)
        )

        # Entry conditions
        if position == 0 and pred_prob[1] >= params.buy_threshold:
            if cash > 0:
                # Calculate shares to buy (considering fees)
                total_shares = cash / effective_price
                fee_shares = total_shares * params.transaction_fee
                shares = total_shares - fee_shares

                # Record buy trade
                new_trade = TradeLog(
                    timestamp=current_time,
                    type="buy",
                    price=effective_price,
                    shares=shares,
                    fee_cash=fee_shares * effective_price,
                    cash_before=cash,
                    cash_after=cash - fee_shares * effective_price,
                    reason="signal",
                )

                cash = 0
                position = 1

        # Exit conditions
        elif position == 1:
            # Stop loss check
            if not last_trade:
                raise ValueError("No previous trade record in position")
            entry_price = last_trade.price
            stop_loss_price = entry_price * (1 - params.stop_loss_pct)

            # First check stop loss condition
            if effective_price < stop_loss_price:
                # Calculate sell amount (considering fees)
                total_cash = shares * effective_price
                fee_cash = total_cash * params.transaction_fee
                cash_after = total_cash - fee_cash

                # Record sell trade
                new_trade = TradeLog(
                    timestamp=current_time,
                    type="sell",
                    price=effective_price,
                    shares=shares,
                    fee_cash=fee_cash,
                    cash_before=shares * entry_price,
                    cash_after=cash_after,
                    reason="stop_loss",
                )

                cash = cash_after
                shares = 0
                position = 0
            # If no stop loss, check prediction signal
            elif pred_prob[0] >= params.sell_threshold:
                # Calculate sell amount (considering fees)
                total_cash = shares * effective_price
                fee_cash = total_cash * params.transaction_fee
                cash_after = total_cash - fee_cash

                # Record sell trade
                new_trade = TradeLog(
                    timestamp=current_time,
                    type="sell",
                    price=effective_price,
                    shares=shares,
                    fee_cash=fee_cash,
                    cash_before=shares * entry_price,
                    cash_after=cash_after,
                    reason="signal",
                )

                cash = cash_after
                shares = 0
                position = 0

        return position, shares, cash, new_trade

    def _update_equity_curve(
        self,
        equity_curve: List[EquityPoint],
        current_time: datetime,
        current_price: float,
        position: int,
        shares: float,
        cash: float,
    ) -> None:
        """
        Update equity curve with current position
        
        Args:
            equity_curve: List of equity points
            current_time: Current timestamp
            current_price: Current price
            position: Current position
            shares: Current shares
            cash: Current cash
        """
        current_equity = cash + shares * current_price
        equity_curve.append(
            EquityPoint(
                time=current_time,
                value=current_equity,
                position=position,
                shares=shares,
                cash=cash,
            )
        )

    def _calculate_metrics(
        self,
        trades: List[TradeLog],
        equity_curve: List[EquityPoint],
        params: BacktestParams,
    ) -> BacktestMetrics:
        """
        Calculate backtesting performance metrics
        
        Args:
            trades: List of trade logs
            equity_curve: List of equity points
            params: Backtest parameters
            
        Returns:
            BacktestMetrics object containing performance metrics
        """
        # Handle insufficient data
        if not equity_curve or len(equity_curve) < 2:
            logger.warning("Equity curve is too short to calculate metrics.")
            annual_periods = self._calculate_annual_periods(params.timeframe)
            return BacktestMetrics(
                timeframe=params.timeframe,
                annual_periods=int(annual_periods),
                initial_balance=params.initial_balance,
                final_balance=params.initial_balance,
                total_return_pct=0.0,
                annualized_return_pct=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown_pct=0.0,
                max_drawdown_duration=0,
                volatility_pct=0.0,
                total_trades=0,
                win_rate_pct=0.0,
                profit_factor=0.0,
                avg_trade_return_pct=0.0,
                avg_winning_trade_pct=0.0,
                avg_losing_trade_pct=0.0,
                avg_holding_period=0,
                max_holding_period=0,
                min_holding_period=0,
                fee_rate=params.transaction_fee,
                total_fees=0.0,
                consecutive_losses=0,
            )

        # Calculate annual periods
        annual_periods = self._calculate_annual_periods(params.timeframe)

        # Calculate basic metrics
        equity_values = np.array([point.value for point in equity_curve])
        initial_balance = equity_curve[0].value
        final_balance = equity_curve[-1].value

        # Handle zero initial balance
        if initial_balance <= 0:
            logger.error("Initial balance is zero or negative, cannot calculate returns.")
            total_return_pct = 0.0
        else:
            total_return_pct = (final_balance / initial_balance - 1) * 100

        # Calculate period returns
        valid_equity_values = equity_values[~np.isnan(equity_values) & (equity_values != 0)]
        if len(valid_equity_values) > 1:
            returns = np.diff(valid_equity_values) / valid_equity_values[:-1]
            returns = np.nan_to_num(returns, nan=0.0, posinf=0.0, neginf=0.0)
        else:
            returns = np.array([])

        # Calculate number of periods
        start_time = equity_curve[0].time
        end_time = equity_curve[-1].time
        if start_time.tzinfo is not None:
            start_time = start_time.tz_localize(None)
        if end_time.tzinfo is not None:
            end_time = end_time.tz_localize(None)

        time_delta_minutes = (end_time - start_time).total_seconds() / 60
        unit = params.timeframe[-1].lower()
        value = int(params.timeframe[:-1])
        if unit == "m":
            minutes_per_period = value
        elif unit == "h":
            minutes_per_period = value * 60
        elif unit == "d":
            minutes_per_period = value * 1440
        else:
            minutes_per_period = 1

        if minutes_per_period > 0:
            periods = time_delta_minutes / minutes_per_period
        else:
            periods = len(returns)

        # Calculate annualized return
        if periods > 0 and initial_balance > 0:
            years = periods / annual_periods
            if years > 0:
                annualized_return_pct = ((final_balance / initial_balance) ** (1 / years) - 1) * 100
            else:
                annualized_return_pct = 0.0
        else:
            annualized_return_pct = 0.0

        # Calculate risk-adjusted returns
        sharpe_ratio = 0.0
        sortino_ratio = 0.0
        volatility_pct = 0.0
        if len(returns) > 1:
            std_returns = np.std(returns)
            if std_returns > 0:
                volatility_pct = std_returns * np.sqrt(annual_periods) * 100

                mean_return_per_period = np.mean(returns)
                risk_free_rate_per_period = params.risk_free_rate / annual_periods
                excess_return_per_period = mean_return_per_period - risk_free_rate_per_period
                sharpe_ratio = (excess_return_per_period / std_returns) * np.sqrt(annual_periods)

                target_returns = returns - risk_free_rate_per_period
                downside_diff = np.minimum(0, target_returns)
                downside_variance = np.mean(downside_diff**2)
                if downside_variance > 0:
                    std_downside = np.sqrt(downside_variance)
                    sortino_ratio = (excess_return_per_period / std_downside) * np.sqrt(annual_periods)
                else:
                    sortino_ratio = 100.0

        # Calculate maximum drawdown
        peak = equity_values[0]
        max_drawdown_pct = 0.0
        drawdown_start_index = 0
        current_drawdown_duration = 0
        max_drawdown_duration = 0

        for i, value in enumerate(equity_values):
            if value >= peak:
                peak = value
                drawdown_start_index = i
                current_drawdown_duration = 0
            else:
                if peak > 0:
                    drawdown = (peak - value) / peak * 100
                    if drawdown > max_drawdown_pct:
                        max_drawdown_pct = drawdown
                current_drawdown_duration = i - drawdown_start_index
                if current_drawdown_duration > max_drawdown_duration:
                    max_drawdown_duration = current_drawdown_duration

        # Calculate trade metrics
        sell_trades = [t for t in trades if t.type in ["sell", "sell_forced"]]
        total_round_trips = len(sell_trades)

        trade_pnls = []
        trade_returns_pct = []
        cost_bases = []
        for trade in sell_trades:
            pnl = trade.cash_after - trade.cash_before
            trade_pnls.append(pnl)
            cost_basis = trade.cash_before
            cost_bases.append(cost_basis)
            if cost_basis > 0:
                trade_return = (pnl / cost_basis) * 100
                trade_returns_pct.append(trade_return)
            else:
                trade_returns_pct.append(0.0)

        winning_trades_count = sum(1 for pnl in trade_pnls if pnl > 0)
        losing_trades_count = sum(1 for pnl in trade_pnls if pnl < 0)

        win_rate_pct = (winning_trades_count / total_round_trips * 100) if total_round_trips > 0 else 0.0

        total_profit = sum(pnl for pnl in trade_pnls if pnl > 0)
        total_loss = abs(sum(pnl for pnl in trade_pnls if pnl < 0))
        if total_profit == 0 and total_loss == 0:
            profit_factor = 1.0
        elif total_loss == 0:
            profit_factor = 100.0
        else:
            profit_factor = total_profit / total_loss

        avg_trade_return_pct = np.mean(trade_returns_pct) if trade_returns_pct else 0.0

        winning_returns = [r for r, pnl in zip(trade_returns_pct, trade_pnls) if pnl > 0]
        losing_returns = [r for r, pnl in zip(trade_returns_pct, trade_pnls) if pnl < 0]

        avg_winning_trade_pct = np.mean(winning_returns) if winning_returns else 0.0
        avg_losing_trade_pct = np.mean(losing_returns) if losing_returns else 0.0

        # Calculate holding periods
        holding_periods = []
        buy_time = None
        for trade in trades:
            if trade.type == "buy":
                buy_time = trade.timestamp
            elif trade.type in ["sell", "sell_forced"] and buy_time:
                sell_time = trade.timestamp
                if buy_time.tzinfo is not None:
                    buy_time = buy_time.tz_localize(None)
                if sell_time.tzinfo is not None:
                    sell_time = sell_time.tz_localize(None)
                holding_periods.append((sell_time - buy_time).total_seconds() / 60)
                buy_time = None

        avg_holding_period = int(np.mean(holding_periods)) if holding_periods else 0
        max_holding_period = int(max(holding_periods)) if holding_periods else 0
        min_holding_period = int(min(holding_periods)) if holding_periods else 0

        # Calculate maximum consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        for pnl in trade_pnls:
            if pnl <= 0:
                consecutive_losses += 1
            else:
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                consecutive_losses = 0
        max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)

        # Calculate total fees
        total_fees = sum(t.fee_cash for t in trades if t.fee_cash is not None and not pd.isna(t.fee_cash))

        # Calculate Calmar ratio
        if max_drawdown_pct > 0:
            calmar_ratio = annualized_return_pct / max_drawdown_pct
        else:
            calmar_ratio = 100.0 if annualized_return_pct > 0 else 0.0

        return BacktestMetrics(
            timeframe=params.timeframe,
            annual_periods=int(annual_periods),
            initial_balance=initial_balance,
            final_balance=final_balance,
            total_return_pct=total_return_pct,
            annualized_return_pct=annualized_return_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown_pct=max_drawdown_pct,
            max_drawdown_duration=max_drawdown_duration,
            volatility_pct=volatility_pct,
            total_trades=total_round_trips,
            win_rate_pct=win_rate_pct,
            profit_factor=profit_factor,
            avg_trade_return_pct=avg_trade_return_pct,
            avg_winning_trade_pct=avg_winning_trade_pct,
            avg_losing_trade_pct=avg_losing_trade_pct,
            avg_holding_period=avg_holding_period,
            max_holding_period=max_holding_period,
            min_holding_period=min_holding_period,
            fee_rate=params.transaction_fee,
            total_fees=total_fees,
            consecutive_losses=max_consecutive_losses,
        )

    def run_backtest(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        price_data: pd.DataFrame,
        model: BaseClassifierModel,
        params: BacktestParams,
    ) -> BacktestResult:
        """
        Run backtesting with specified parameters
        
        Args:
            X: Feature data
            y: Target variable
            price_data: Price data
            model: Model to use for predictions
            params: Backtest parameters
            
        Returns:
            BacktestResult object containing backtest results
        """
        # Log backtest parameters
        logger.info("Backtest parameters:")
        logger.info(f"Symbol: {params.symbol}")
        logger.info(f"Timeframe: {params.timeframe}")
        logger.info(f"Start date: {params.start_timestamp}")
        logger.info(f"End date: {params.end_timestamp}")
        logger.info(f"Technical indicators: {params.ta_indicators}")
        logger.info(f"Lookback periods: {params.look_back}")
        logger.info(f"Model name: {params.model_name}")
        logger.info(f"Model parameters: {params.model_params}")
        logger.info(f"Retrain interval: {params.retrain_interval}")
        logger.info(f"Training window size: {params.window_size}")
        logger.info(f"Buy threshold: {params.buy_threshold}")
        logger.info(f"Sell threshold: {params.sell_threshold}")
        logger.info(f"Stop loss percentage: {params.stop_loss_pct}")
        logger.info(f"Initial balance: {params.initial_balance}")
        logger.info(f"Transaction fee: {params.transaction_fee}")
        logger.info(f"Max position size: {params.max_position_size}")
        logger.info(f"Min position size: {params.min_position_size}")
        logger.info(f"Risk-free rate: {params.risk_free_rate}")
        logger.info(f"Slippage: {params.slippage}")

        # Validate input data
        self._validate_input_data(X, y, price_data)

        # Initialize variables
        initial_balance = params.initial_balance
        cash = initial_balance
        shares = 0
        position = 0
        trades: List[TradeLog] = []
        equity_curve: List[EquityPoint] = []

        # Convert string timestamps to datetime objects
        start_timestamp = pd.to_datetime(params.start_timestamp).tz_localize(None)
        end_timestamp = pd.to_datetime(params.end_timestamp).tz_localize(None)

        # Add initial equity point
        self._update_equity_curve(equity_curve, start_timestamp, price_data.loc[start_timestamp, "close"], position, shares, cash)
        
        # Get training set indices
        train_end_index = X.index.get_loc(start_timestamp)
        train_start_index = train_end_index - params.window_size

        # Get backtest end index
        backtest_end_index = X.index.get_loc(end_timestamp)

        # Start rolling training
        while train_end_index <= backtest_end_index:
            # Get training set
            X_train = X.iloc[train_start_index:train_end_index]
            y_train = y.iloc[train_start_index:train_end_index]

            # Log training set information
            logger.info(f"Training set time range: {X_train.index[0]} - {X_train.index[-1]}")
            logger.info(f"Training set shape: {X_train.shape}")

            # Standardize training set
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)

            # Ensure y is numpy array
            y_train_values = y_train.values.astype(np.int32)

            # Train model
            model.fit(X_train_scaled, y_train_values)

            # Get backtest set
            test_start_index = train_end_index
            test_end_index = min(test_start_index + params.retrain_interval, backtest_end_index + 1)
            X_test = X.iloc[test_start_index:test_end_index]

            # Standardize test set
            X_test_scaled = scaler.transform(X_test)

            # Log test set information
            logger.info(f"Test set time range: {X_test.index[0]} - {X_test.index[-1]}")
            logger.info(f"Test set shape: {X_test.shape}")

            # Predict on backtest set
            pred_probs = model.predict_proba(X_test_scaled)

            # Execute trades
            for i in range(len(pred_probs)):
                current_time = X_test.index[i]
                current_price = price_data.loc[current_time, "close"]
                position, shares, cash, new_trade = self._execute_trade(
                    current_time,
                    current_price,
                    position,
                    shares,
                    cash,
                    pred_probs[i],
                    params,
                    last_trade=trades[-1] if trades else None,
                )
                if new_trade:
                    trades.append(new_trade)
                
                # Force close position at end of backtest
                if current_time == X.index[backtest_end_index] and position == 1:
                    current_price = price_data.loc[current_time, "close"]
                    effective_price = current_price * (1 - params.slippage)
                    total_cash = shares * effective_price
                    fee_cash = total_cash * params.transaction_fee
                    cash_after = total_cash - fee_cash
                    trades.append(TradeLog(
                        timestamp=current_time,
                        type="sell_forced",
                        price=effective_price,
                        shares=shares,
                        fee_cash=fee_cash,
                        cash_before=shares * trades[-1].price,
                        cash_after=cash_after,
                        reason="forced_close",
                    ))
                    position = 0
                    shares = 0
                    cash = cash_after

                # Update equity curve
                self._update_equity_curve(equity_curve, current_time, current_price, position, shares, cash)

            # Update training set indices
            train_end_index = test_end_index
            train_start_index = train_end_index - params.window_size

        # Calculate metrics
        metrics = self._calculate_metrics(trades, equity_curve, params)

        # Return backtest result
        return BacktestResult(
            metrics=metrics,
            trade_logs=trades,
            equity_curve=equity_curve
        )