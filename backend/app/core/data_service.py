import ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, insert
import logging

from app.db.models import OHLCVData
from app.schemas.data import DataFetchRequest, OHLCVData as OHLCVDataSchema
from app.schemas.common import ResponseModel

# Configure logging
logger = logging.getLogger(__name__)

class DataService:
    """Service for fetching and managing market data"""
    
    def __init__(self, db: Session):
        """
        Initialize the data service
        
        Args:
            db: Database session
        """
        self.db = db
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        logger.info("DataService initialized")

    def _get_timeframe_minutes(self, timeframe: str) -> int:
        """
        Convert timeframe string to minutes
        
        Args:
            timeframe: Timeframe string (e.g., '1m', '1h', '1d')
            
        Returns:
            int: Number of minutes
            
        Raises:
            ValueError: If timeframe format is invalid
        """
        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 60 * 24
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

    def _store_ohlcv_data(self, df: pd.DataFrame) -> int:
        """
        Store OHLCV data in database, automatically ignoring duplicates
        
        Args:
            df: DataFrame containing OHLCV data
            
        Returns:
            int: Number of records actually stored
        """
        if df.empty:
            logger.warning("Attempting to store empty data")
            return 0
            
        symbol = df['symbol'].iloc[0]
        timeframe = df['timeframe'].iloc[0]
        logger.info(f"Starting data storage - Symbol: {symbol}, Timeframe: {timeframe}, Records: {len(df)}")
        
        # Prepare data for batch insert
        data = df[['symbol', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
        
        try:
            # Get record count before insert
            before_count = self.db.query(func.count(OHLCVData.id)).filter(
                OHLCVData.symbol == symbol,
                OHLCVData.timeframe == timeframe
            ).scalar()
            
            # Batch insert with ignore duplicates
            stmt = insert(OHLCVData).prefix_with('OR IGNORE')
            self.db.execute(stmt, data)
            self.db.commit()
            
            # Get record count after insert
            after_count = self.db.query(func.count(OHLCVData.id)).filter(
                OHLCVData.symbol == symbol,
                OHLCVData.timeframe == timeframe
            ).scalar()
            
            # Calculate actual inserted records
            stored_count = after_count - before_count
            logger.info(f"Data storage completed - Symbol: {symbol}, Timeframe: {timeframe}, Stored: {stored_count}, Skipped: {len(data) - stored_count}")
            return stored_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Data storage failed: {str(e)}")
            return 0

    def _fetch_ohlcv_batch(
        self, 
        symbol: str, 
        timeframe: str, 
        start_time: datetime, 
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch a batch of OHLCV data
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            start_time: Start time for data fetch
            limit: Maximum number of records to fetch
            
        Returns:
            pd.DataFrame: OHLCV data
        """
        logger.info(f"Starting data fetch - Symbol: {symbol}, Timeframe: {timeframe}, Start time: {start_time}")
        
        ohlcv = self.exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            since=int(start_time.timestamp() * 1000),
            limit=limit
        )
        
        if not ohlcv:
            logger.warning(f"No data fetched - Symbol: {symbol}, Timeframe: {timeframe}, Start time: {start_time}")
            return pd.DataFrame()
            
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df['symbol'] = symbol
        df['timeframe'] = timeframe
        
        logger.info(f"Data fetch successful - Symbol: {symbol}, Timeframe: {timeframe}, Records: {len(df)}")
        return df

    def fetch_and_store_data(self, request: DataFetchRequest) -> ResponseModel[Dict]:
        """
        Fetch data from Binance and store in database
        
        Args:
            request: Data fetch request parameters
            
        Returns:
            ResponseModel containing fetch results
        """
        try:
            logger.info(f"Processing data fetch request - Symbol: {request.symbol}, Timeframe: {request.timeframe}")

            # Ensure timezone awareness
            if request.start_timestamp.tzinfo is None:
                request.start_timestamp = request.start_timestamp.replace(tzinfo=timezone.utc)
            if request.end_timestamp.tzinfo is None:
                request.end_timestamp = request.end_timestamp.replace(tzinfo=timezone.utc)
            
            # Check existing data range in database
            existing_data = self._get_existing_data_range(request.symbol, request.timeframe)
            if existing_data is not None:
                logger.info(f"Existing data range: {existing_data[0].isoformat()} to {existing_data[1].isoformat()}")
                
                # Determine fetch range
                fetch_range = self._determine_fetch_range(
                    request.start_timestamp, 
                    request.end_timestamp, 
                    existing_data
                )

                if fetch_range is None:
                    logger.info("Data already exists, no update needed")
                    return ResponseModel(
                        success=True,
                        data={
                            "message": "Data already exists, no update needed",
                            "existing_data": existing_data
                        },
                        message="Data already exists"
                    )
                
                fetch_start, fetch_end = fetch_range
            else:
                fetch_start = request.start_timestamp
                fetch_end = request.end_timestamp
            
            logger.info(f"Fetch range - Start: {fetch_start}, End: {fetch_end}")

            # Calculate total data points needed
            time_diff = fetch_end - fetch_start
            timeframe_minutes = self._get_timeframe_minutes(request.timeframe)
            total_points = int(time_diff.total_seconds() / (timeframe_minutes * 60))
            logger.info(f"Total data points needed: {total_points}")
            
            total_fetched = 0
            current_start = fetch_start
            
            while current_start < fetch_end:
                logger.info(f"Fetching batch - Current start time: {current_start}")
                
                # Fetch batch of data
                df = self._fetch_ohlcv_batch(
                    request.symbol,
                    request.timeframe,
                    current_start
                )
                
                if df.empty:
                    logger.warning("Empty data received, breaking loop")
                    break
                
                # Store in database
                batch_size = self._store_ohlcv_data(df)
                total_fetched += batch_size
                logger.info(f"Batch processed - Fetched: {batch_size}, Total: {total_fetched}")
                
                # Update next fetch start time
                current_start = df['timestamp'].max() + pd.Timedelta(minutes=timeframe_minutes)
                
                # Break if we have enough data
                if total_points <= 1000 and total_fetched >= total_points:
                    logger.info("Enough data points fetched, breaking loop")
                    break
            
            self.db.commit()
            logger.info(f"Data fetch and storage completed - Total records: {total_fetched}")
            
            return ResponseModel(
                success=True,
                data={
                    "message": "Data fetch and storage successful",
                    "fetched_records": total_fetched,
                    "time_range": {
                        "start": fetch_start,
                        "end": fetch_end
                    }
                },
                message="Data fetch and storage successful"
            )

        except Exception as e:
            logger.error(f"Data fetch and storage failed: {str(e)}", exc_info=True)
            self.db.rollback()
            return ResponseModel(
                success=False,
                data={},
                message=f"Data fetch failed: {str(e)}"
            )

    def get_available_data(self) -> ResponseModel[List[Dict]]:
        """
        Get available data ranges from database
        
        Returns:
            ResponseModel containing available data ranges for each symbol and timeframe
        """
        try:
            logger.info("Getting available data ranges")
            
            # Query min and max timestamps for each symbol and timeframe
            query = self.db.query(
                OHLCVData.symbol,
                OHLCVData.timeframe,
                func.min(OHLCVData.timestamp).label('min_date'),
                func.max(OHLCVData.timestamp).label('max_date'),
                func.count(OHLCVData.timestamp).label('data_points')
            ).group_by(
                OHLCVData.symbol,
                OHLCVData.timeframe
            )

            results = query.all()
            
            if not results:
                logger.info("No data available in database")
                return ResponseModel(
                    success=True,
                    data=[],
                    message="No data available in database"
                )
            
            # Convert to response format
            available_data = []
            for r in results:
                available_data.append({
                    "symbol": r.symbol,
                    "timeframe": r.timeframe,
                    "start_timestamp": r.min_date,
                    "end_timestamp": r.max_date,
                    "data_points": r.data_points
                })
            
            logger.info(f"Successfully retrieved available data ranges - Count: {len(available_data)}")
            
            return ResponseModel(
                success=True,
                data=available_data,
                message="Successfully retrieved available data ranges"
            )

        except Exception as e:
            logger.error(f"Failed to get available data: {str(e)}", exc_info=True)
            return ResponseModel(
                success=False,
                data=[],
                message=f"Failed to get available data: {str(e)}"
            )

    def get_ohlcv_data(
        self, 
        symbol: str, 
        timeframe: str, 
        start_timestamp: datetime, 
        end_timestamp: datetime
    ) -> ResponseModel[List[OHLCVDataSchema]]:
        """
        Get OHLCV data for specified range
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            start_timestamp: Start date
            end_timestamp: End date
            
        Returns:
            ResponseModel containing OHLCV data
        """
        try:
            logger.info(f"Querying OHLCV data - Symbol: {symbol}, Timeframe: {timeframe}, Range: {start_timestamp} to {end_timestamp}")
            
            # Ensure timezone awareness
            if start_timestamp.tzinfo is None:
                start_timestamp = start_timestamp.replace(tzinfo=timezone.utc)
            if end_timestamp.tzinfo is None:
                end_timestamp = end_timestamp.replace(tzinfo=timezone.utc)
            
            # Fetch and store data if needed
            fetch_request = DataFetchRequest(
                symbol=symbol,
                timeframe=timeframe,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp
            )
            
            fetch_response = self.fetch_and_store_data(fetch_request)
            
            if not fetch_response.success:
                logger.error(f"Data fetch and storage failed: {fetch_response.message}")
                return ResponseModel(
                    success=False,
                    data=[],
                    message=f"Data fetch and storage failed: {fetch_response.message}"
                )
            
            # Query data from database
            query = self.db.query(OHLCVData).filter(
                and_(
                    OHLCVData.symbol == symbol,
                    OHLCVData.timeframe == timeframe,
                    OHLCVData.timestamp >= start_timestamp,
                    OHLCVData.timestamp <= end_timestamp
                )
            ).order_by(OHLCVData.timestamp)

            results = query.all()
            
            logger.info(f"Successfully queried data - Symbol: {symbol}, Timeframe: {timeframe}, Records: {len(results)}")
            
            data = [OHLCVDataSchema(
                timestamp=r.timestamp,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume
            ) for r in results]

            return ResponseModel(
                success=True,
                data=data,
                message=f"Successfully retrieved {len(data)} OHLCV records"
            )

        except Exception as e:
            logger.error(f"Failed to get OHLCV data: {str(e)}", exc_info=True)
            return ResponseModel(
                success=False,
                data=[],
                message=f"Failed to get OHLCV data: {str(e)}"
            )

    def _get_existing_data_range(
        self, 
        symbol: str, 
        timeframe: str
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Get existing data range from database
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            
        Returns:
            Optional tuple of (start_timestamp, end_timestamp) if data exists
        """
        result = self.db.query(
            func.min(OHLCVData.timestamp).label('min_date'),
            func.max(OHLCVData.timestamp).label('max_date')
        ).filter(
            and_(
                OHLCVData.symbol == symbol,
                OHLCVData.timeframe == timeframe
            )
        ).first()

        if result and result.min_date and result.max_date:
            return (
                result.min_date.replace(tzinfo=timezone.utc),
                result.max_date.replace(tzinfo=timezone.utc)
            )
        return None

    def _determine_fetch_range(
        self, 
        requested_start: datetime, 
        requested_end: datetime, 
        existing_range: Optional[Tuple[datetime, datetime]]
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Determine data fetch range ensuring continuity
        
        Args:
            requested_start: Requested start date
            requested_end: Requested end date
            existing_range: Existing data range
            
        Returns:
            Optional tuple of (start_timestamp, end_timestamp) if fetch needed
        """
        # Ensure timezone awareness
        if requested_start.tzinfo is None:
            requested_start = requested_start.replace(tzinfo=timezone.utc)
        if requested_end.tzinfo is None:
            requested_end = requested_end.replace(tzinfo=timezone.utc)

        if not existing_range:
            return requested_start, requested_end

        existing_start, existing_end = existing_range
        
        # Check if requested range is within existing data
        if requested_start >= existing_start and requested_end <= existing_end:
            return None

        # Determine fetch range ensuring continuity
        if requested_end < existing_start:
            return requested_start, existing_start
        elif requested_end >= existing_start and requested_end <= existing_end:
            if requested_start <= existing_start:
                return requested_start, existing_start
            else:
                return None
        elif requested_end > existing_end:
            return existing_end, requested_end

