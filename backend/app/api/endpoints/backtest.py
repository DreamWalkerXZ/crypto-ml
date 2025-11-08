from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import pandas as pd
from app.db import get_crypto_db, get_backtest_db, BacktestParams as BacktestParamsModel, BacktestResult as BacktestResultModel
from app.core.data_service import DataService
from app.core.preprocessing_service import PreprocessingService
from app.core.modeling_service import get_model
from app.core.backtesting_service import BacktestingService
from app.core.task_service import task_service, TaskStatus
from app.schemas.backtest import BacktestParams, BacktestResult
from app.schemas.common import ResponseModel
import logging
import json
import uuid
logger = logging.getLogger(__name__)

# Create router for backtest-related endpoints
router = APIRouter()

def serialize_timestamp(timestamp):
    """Convert timestamp object to ISO format string"""
    if isinstance(timestamp, pd.Timestamp):
        return timestamp.isoformat()
    elif isinstance(timestamp, datetime):
        return timestamp.isoformat()
    return timestamp

def serialize_for_db(obj):
    """Serialize object to database-compatible format"""
    if isinstance(obj, dict):
        return {k: serialize_for_db(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_db(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, datetime)):
        return serialize_timestamp(obj)
    elif hasattr(obj, 'model_dump'):
        return serialize_for_db(obj.model_dump())
    return obj

def run_background_backtest(task_id: str, params: BacktestParams, crypto_db: Session, backtest_db: Session):
    """Run backtest task in background"""
    try:
        # Update task status to running
        task_service.update_task_status(task_id, TaskStatus.RUNNING)
        
        # Initialize services
        data_service = DataService(crypto_db)
        preprocessing_service = PreprocessingService()
        backtesting_service = BacktestingService()

        # Convert date string to datetime object and ensure it has timezone information
        start_timestamp = datetime.fromisoformat(params.start_timestamp)
        end_timestamp = datetime.fromisoformat(params.end_timestamp)
        if start_timestamp.tzinfo is None:
            start_timestamp = start_timestamp.replace(tzinfo=timezone.utc)
        if end_timestamp.tzinfo is None:
            end_timestamp = end_timestamp.replace(tzinfo=timezone.utc)

        # 1. Get data
        logger.info(f"Getting data: {params.symbol}, {params.timeframe}, {start_timestamp - timedelta(days=9*30)}, {end_timestamp}")
        data_response = data_service.get_ohlcv_data(
            params.symbol,
            params.timeframe,
            start_timestamp - timedelta(days=9*30),
            end_timestamp + timedelta(days=9*30)
        )
        
        if not data_response.success:
            task_service.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error=f"Failed to get data: {data_response.message}"
            )
            return
        
        # Convert OHLCV data list to DataFrame
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'open': d.open,
            'high': d.high,
            'low': d.low,
            'close': d.close,
            'volume': d.volume
        } for d in data_response.data])
        
        # 2. Preprocess data
        X, y, price_data = preprocessing_service.prepare_features_and_target(
            df,
            params.ta_indicators,
            params.look_back,
            params.prediction_horizon,
            params.price_change_threshold
        )
        
        # 3. Get model
        model_params = params.model_params or {}
        input_size = None
        if params.model_name.startswith("PyTorch"):
            input_size = len(X.columns)
        
        model = get_model(params.model_name, input_size=input_size, **model_params)
        
        # 4. Run backtest
        result = backtesting_service.run_backtest(
            X, y, price_data, model, params
        )
        
        # Generate unique backtest ID
        backtest_id = str(uuid.uuid4())

        # Combine model_params and default_params
        model_params = {**model_params, **model.DEFAULT_MODEL_PARAMS}
        
        # Save backtest parameters to database
        backtest_params = BacktestParamsModel(
            id=backtest_id,
            symbol=params.symbol,
            timeframe=params.timeframe,
            start_timestamp=datetime.fromisoformat(params.start_timestamp.replace('Z', '+00:00')),
            end_timestamp=datetime.fromisoformat(params.end_timestamp.replace('Z', '+00:00')),
            ta_indicators=params.ta_indicators,
            look_back=params.look_back,
            prediction_horizon=params.prediction_horizon,
            price_change_threshold=params.price_change_threshold,
            model_name=params.model_name,
            model_params=model_params,
            retrain_interval=params.retrain_interval,
            window_size=params.window_size,
            buy_threshold=params.buy_threshold,
            sell_threshold=params.sell_threshold,
            stop_loss_pct=params.stop_loss_pct,
            initial_balance=params.initial_balance,
            transaction_fee=params.transaction_fee,
            slippage=params.slippage,
            risk_free_rate=params.risk_free_rate
        )
        backtest_db.add(backtest_params)
        backtest_db.commit()
        
        # Save backtest results to database
        metrics = result.metrics.model_dump()
        backtest_result = BacktestResultModel(
            id=str(uuid.uuid4()),
            params_id=backtest_id,
            
            # Basic information
            timeframe=metrics['timeframe'],
            annual_periods=metrics['annual_periods'],
            initial_balance=metrics['initial_balance'],
            final_balance=metrics['final_balance'],
            
            # Return metrics
            total_return_pct=metrics['total_return_pct'],
            annualized_return_pct=metrics['annualized_return_pct'],
            sharpe_ratio=metrics['sharpe_ratio'],
            sortino_ratio=metrics['sortino_ratio'],
            calmar_ratio=metrics['calmar_ratio'],
            
            # Risk metrics
            max_drawdown_pct=metrics['max_drawdown_pct'],
            max_drawdown_duration=metrics['max_drawdown_duration'],
            volatility_pct=metrics['volatility_pct'],
            
            # Trading metrics
            total_trades=metrics['total_trades'],
            win_rate_pct=metrics['win_rate_pct'],
            profit_factor=metrics['profit_factor'],
            avg_trade_return_pct=metrics['avg_trade_return_pct'],
            avg_winning_trade_pct=metrics['avg_winning_trade_pct'],
            avg_losing_trade_pct=metrics['avg_losing_trade_pct'],
            
            # Position metrics
            avg_holding_period=metrics['avg_holding_period'],
            max_holding_period=metrics['max_holding_period'],
            min_holding_period=metrics['min_holding_period'],
            
            # Other metrics
            fee_rate=metrics['fee_rate'],
            total_fees=metrics['total_fees'],
            consecutive_losses=metrics['consecutive_losses'],
            
            # Trade logs and equity curve
            trade_logs=serialize_for_db([trade.model_dump() for trade in result.trade_logs]),
            equity_curve=serialize_for_db([point.model_dump() for point in result.equity_curve])
        )
        backtest_db.add(backtest_result)
        backtest_db.commit()
        
        # Update task status to completed
        task_service.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
        
    except Exception as e:
        logger.error(f"Backtest task failed: {str(e)}")
        task_service.update_task_status(
            task_id, 
            TaskStatus.FAILED, 
            error=str(e)
        )

@router.post("/run", response_model=ResponseModel[dict])
async def run_backtest(
    params: BacktestParams, 
    background_tasks: BackgroundTasks,
    crypto_db: Session = Depends(get_crypto_db),
    backtest_db: Session = Depends(get_backtest_db)
):
    """Start backtest task"""
    try:
        # Create new task
        task_id = task_service.create_task(params.model_dump())
        
        # Add backtest task to background task queue
        background_tasks.add_task(run_background_backtest, task_id, params, crypto_db, backtest_db)
        
        return ResponseModel(
            success=True,
            data={"task_id": task_id},
            message="Backtest task started"
        )
    except Exception as e:
        return ResponseModel(
            success=False,
            data=None,
            message=f"Failed to start backtest task: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=ResponseModel[dict])
async def get_backtest_status(task_id: str):
    """Get backtest task status"""
    task = task_service.get_task(task_id)
    if not task:
        return ResponseModel(
            success=False,
            data=None,
            message=f"Task ID not found: {task_id}"
        )
    
    response_data = {
        "task_id": task.task_id,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
    }
    
    if task.started_at:
        response_data["started_at"] = task.started_at.isoformat()
    if task.completed_at:
        response_data["completed_at"] = task.completed_at.isoformat()
    if task.error:
        response_data["error"] = task.error
    if task.result:
        response_data["result"] = task.result.model_dump()
    
    return ResponseModel(
        success=True,
        data=response_data,
        message="Task status retrieved successfully"
    )

@router.get("/tasks", response_model=ResponseModel[list])
async def list_tasks():
    """Get all task list"""
    tasks = []
    for task in task_service.tasks.values():
        task_data = {
            "task_id": task.task_id,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
        }
        
        if task.started_at:
            task_data["started_at"] = task.started_at.isoformat()
        if task.completed_at:
            task_data["completed_at"] = task.completed_at.isoformat()
        if task.error:
            task_data["error"] = task.error
        
        tasks.append(task_data)
    
    return ResponseModel(
        success=True,
        data=tasks,
        message="Task list retrieved successfully"
    )

@router.get("/results/{backtest_id}", response_model=ResponseModel[dict])
async def get_backtest_results(
    backtest_id: str,
    backtest_db: Session = Depends(get_backtest_db)
):
    """Get backtest results"""
    try:
        # Query backtest results first
        result = backtest_db.query(BacktestResultModel).filter(BacktestResultModel.id == backtest_id).first()
        if not result:
            return ResponseModel(
                success=False,
                data=None,
                message=f"Backtest results not found, ID: {backtest_id}"
            )
        
        # Query backtest parameters using params_id
        params = backtest_db.query(BacktestParamsModel).filter(BacktestParamsModel.id == result.params_id).first()
        if not params:
            return ResponseModel(
                success=False,
                data=None,
                message=f"Backtest parameters not found for result ID: {backtest_id}"
            )
        
        # Build response data
        response_data = {
            "params": {
                "id": params.id,
                "symbol": params.symbol,
                "timeframe": params.timeframe,
                "start_timestamp": params.start_timestamp.isoformat(),
                "end_timestamp": params.end_timestamp.isoformat(),
                "ta_indicators": params.ta_indicators,
                "look_back": params.look_back,
                "prediction_horizon": params.prediction_horizon,
                "price_change_threshold": params.price_change_threshold,
                "model_name": params.model_name,
                "model_params": params.model_params,
                "retrain_interval": params.retrain_interval,
                "window_size": params.window_size,
                "buy_threshold": params.buy_threshold,
                "sell_threshold": params.sell_threshold,
                "stop_loss_pct": params.stop_loss_pct,
                "initial_balance": params.initial_balance,
                "transaction_fee": params.transaction_fee,
                "slippage": params.slippage,
                "risk_free_rate": params.risk_free_rate,
                "created_at": params.created_at.isoformat()
            },
            "results": {
                "id": result.id,
                "timeframe": result.timeframe,
                "annual_periods": result.annual_periods,
                "initial_balance": result.initial_balance,
                "final_balance": result.final_balance,
                "total_return_pct": result.total_return_pct,
                "annualized_return_pct": result.annualized_return_pct,
                "sharpe_ratio": result.sharpe_ratio,
                "sortino_ratio": result.sortino_ratio,
                "calmar_ratio": result.calmar_ratio,
                "max_drawdown_pct": result.max_drawdown_pct,
                "max_drawdown_duration": result.max_drawdown_duration,
                "volatility_pct": result.volatility_pct,
                "total_trades": result.total_trades,
                "win_rate_pct": result.win_rate_pct,
                "profit_factor": result.profit_factor,
                "avg_trade_return_pct": result.avg_trade_return_pct,
                "avg_winning_trade_pct": result.avg_winning_trade_pct,
                "avg_losing_trade_pct": result.avg_losing_trade_pct,
                "avg_holding_period": result.avg_holding_period,
                "max_holding_period": result.max_holding_period,
                "min_holding_period": result.min_holding_period,
                "fee_rate": result.fee_rate,
                "total_fees": result.total_fees,
                "consecutive_losses": result.consecutive_losses,
                "trade_logs": result.trade_logs,
                "equity_curve": result.equity_curve,
                "created_at": result.created_at.isoformat()
            }
        }
        
        return ResponseModel(
            success=True,
            data=response_data,
            message="Backtest results retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get backtest results: {str(e)}")
        return ResponseModel(
            success=False,
            data=None,
            message=f"Failed to get backtest results: {str(e)}"
        )

@router.get("/results", response_model=ResponseModel[list])
async def list_backtest_results(
    backtest_db: Session = Depends(get_backtest_db)
):
    """Get all backtest results list"""
    try:
        # Query all backtest results
        results = backtest_db.query(
            BacktestResultModel.id,
            BacktestParamsModel.symbol,
            BacktestParamsModel.timeframe,
            BacktestParamsModel.model_name,
            BacktestParamsModel.start_timestamp,
            BacktestParamsModel.end_timestamp,
            BacktestResultModel.total_return_pct,
            BacktestResultModel.annualized_return_pct,
            BacktestResultModel.sharpe_ratio,
            BacktestResultModel.win_rate_pct,
            BacktestResultModel.created_at
        ).join(
            BacktestParamsModel,
            BacktestParamsModel.id == BacktestResultModel.params_id
        ).all()
        
        # Build response data
        response_data = [{
            "id": result.id,
            "symbol": result.symbol,
            "timeframe": result.timeframe,
            "model_name": result.model_name,
            "start_timestamp": result.start_timestamp.isoformat(),
            "end_timestamp": result.end_timestamp.isoformat(),
            "total_return_pct": result.total_return_pct,
            "annualized_return_pct": result.annualized_return_pct,
            "sharpe_ratio": result.sharpe_ratio,
            "win_rate_pct": result.win_rate_pct,
            "created_at": result.created_at.isoformat()
        } for result in results]
        
        return ResponseModel(
            success=True,
            data=response_data,
            message="Backtest results list retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get backtest results list: {str(e)}")
        return ResponseModel(
            success=False,
            data=None,
            message=f"Failed to get backtest results list: {str(e)}"
        ) 