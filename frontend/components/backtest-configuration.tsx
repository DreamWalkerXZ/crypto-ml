"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"
import { AvailableDataResponse, ModelInfo, BacktestParams } from "@/lib/types"
import { TimeInput } from "@/components/time-input"
import { runBacktest } from "@/lib/api"

// Constants
const DEFAULT_VALUES = {
  // Data selection
  baseSymbol: "BTC",
  quoteSymbol: "USDT",
  timeframe: "1h",
  
  // Feature engineering
  lookBack: 20,
  predictionHorizon: 5,
  priceChangeThreshold: 0.2,
  windowSize: 100,
  
  // Model configuration
  retrainInterval: 168,
  
  // Trading parameters
  buyThreshold: 60,
  sellThreshold: 50,
  stopLossPct: 5,
  initialBalance: 10000,
  transactionFee: 0.1,
  slippage: 0.1,
  riskFreeRate: 2.0,
}

const AVAILABLE_INDICATORS = [
  { id: "RSI_14", label: "Relative Strength Index, 14 periods" },
  { id: "MACD_12_26_9", label: "Moving Average Convergence Divergence, 12,26,9" },
  { id: "BBANDS_20_2_2", label: "Bollinger Bands, 20 periods, 2 standard deviations" },
  { id: "ATR_14", label: "Average True Range, 14 periods" },
  { id: "ADX_14", label: "Average Directional Index, 14 periods" },
  { id: "EMA_10", label: "Exponential Moving Average, 10 periods" },
  { id: "SMA_10", label: "Simple Moving Average, 10 periods" },
  { id: "EMA_20", label: "Exponential Moving Average, 20 periods" },
  { id: "SMA_20", label: "Simple Moving Average, 20 periods" },
  { id: "EMA_30", label: "Exponential Moving Average, 30 periods" },
  { id: "SMA_30", label: "Simple Moving Average, 30 periods" },
] as const

interface BacktestConfigurationProps {
  availableData: AvailableDataResponse[];
  availableModels: {
    success: boolean;
    data: ModelInfo[];
    message?: string;
  };
}

export default function BacktestConfiguration({ availableData, availableModels }: BacktestConfigurationProps) {
  const [isLoading, setIsLoading] = useState(false)
  const models = availableModels.data || []

  // Data selection states
  const [baseSymbol, setBaseSymbol] = useState(DEFAULT_VALUES.baseSymbol)
  const [quoteSymbol, setQuoteSymbol] = useState(DEFAULT_VALUES.quoteSymbol)
  const [timeframe, setTimeframe] = useState(DEFAULT_VALUES.timeframe)
  const [startTimestamp, setStartTimestamp] = useState("")
  const [endTimestamp, setEndTimestamp] = useState("")

  // Feature engineering states
  const [indicators, setIndicators] = useState<string[]>([])
  const [lookBack, setLookBack] = useState(DEFAULT_VALUES.lookBack)
  const [predictionHorizon, setPredictionHorizon] = useState(DEFAULT_VALUES.predictionHorizon)
  const [priceChangeThreshold, setPriceChangeThreshold] = useState(DEFAULT_VALUES.priceChangeThreshold)
  
  // Model configuration states
  const [windowSize, setWindowSize] = useState(DEFAULT_VALUES.windowSize)
  const [retrainInterval, setRetrainInterval] = useState(DEFAULT_VALUES.retrainInterval)
  const [modelName, setModelName] = useState(models[0]?.name || "")
  const [modelParams, setModelParams] = useState(
    models[0] ? JSON.stringify(models[0].default_params, null, 2) : "{}"
  )

  // Trading parameters states
  const [buyThreshold, setBuyThreshold] = useState(DEFAULT_VALUES.buyThreshold)
  const [sellThreshold, setSellThreshold] = useState(DEFAULT_VALUES.sellThreshold)
  const [stopLossPct, setStopLossPct] = useState(DEFAULT_VALUES.stopLossPct)
  const [initialBalance, setInitialBalance] = useState(DEFAULT_VALUES.initialBalance)
  const [transactionFee, setTransactionFee] = useState(DEFAULT_VALUES.transactionFee)
  const [slippage, setSlippage] = useState(DEFAULT_VALUES.slippage)
  const [riskFreeRate, setRiskFreeRate] = useState(DEFAULT_VALUES.riskFreeRate)
  const [maxPositionSize, setMaxPositionSize] = useState<number | null>(null)
  const [minPositionSize, setMinPositionSize] = useState<number | null>(null)

  // Event handlers
  const handleIndicatorChange = (id: string, checked: boolean) => {
    setIndicators(prev => 
      checked ? [...prev, id] : prev.filter(item => item !== id)
    )
  }

  const handleSelectAllIndicators = (checked: boolean) => {
    setIndicators(checked ? AVAILABLE_INDICATORS.map(indicator => indicator.id) : [])
  }

  const handleModelChange = (value: string) => {
    setModelName(value)
    const model = models.find(m => m.name === value)
    if (model) {
      setModelParams(JSON.stringify(model.default_params, null, 2))
    }
  }

  const handleModelParamsChange = (value: string) => {
    setModelParams(value)
    try {
      JSON.parse(value)
    } catch (error) {
      toast.error("Please enter valid JSON format")
    }
  }

  const validateBacktestParams = (): boolean => {
    if (!startTimestamp || !endTimestamp) {
      toast.error("Please select start and end timestamps")
      return false
    }

    if (indicators.length === 0) {
      toast.error("Please select at least one technical indicator")
      return false
    }

    if (!modelName) {
      toast.error("Please select a model")
      return false
    }

    try {
      JSON.parse(modelParams)
    } catch (error) {
      toast.error("Model parameters must be in valid JSON format")
      return false
    }

    return true
  }

  const handleRunBacktest = async () => {
    if (!validateBacktestParams()) return

    setIsLoading(true)

    try {
      const backtestParams: BacktestParams = {
        symbol: `${baseSymbol}/${quoteSymbol}`,
        timeframe,
        start_timestamp: startTimestamp,
        end_timestamp: endTimestamp,
        ta_indicators: indicators,
        look_back: lookBack,
        prediction_horizon: predictionHorizon,
        price_change_threshold: priceChangeThreshold / 100,
        model_name: modelName,
        model_params: JSON.parse(modelParams),
        retrain_interval: retrainInterval,
        window_size: windowSize,
        buy_threshold: buyThreshold / 100,
        sell_threshold: sellThreshold / 100,
        stop_loss_pct: stopLossPct / 100,
        initial_balance: initialBalance,
        transaction_fee: transactionFee / 100,
        slippage: slippage / 100,
        risk_free_rate: riskFreeRate / 100,
        max_position_size: maxPositionSize,
        min_position_size: minPositionSize
      }

      const response = await runBacktest(backtestParams)
      
      if (response.success) {
        toast.success(`Backtest task started. Task ID: ${response.data.task_id}`)
      } else {
        toast.error(response.message || "Failed to start backtest task")
      }
    } catch (error) {
      toast.error("Error starting backtest task. Please try again")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        {/* Data Selection Card */}
        <Card>
          <CardHeader>
            <CardTitle>Data Selection</CardTitle>
            <CardDescription>Select the cryptocurrency and time period for backtesting</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Trading Pair</Label>
              <div className="flex items-center gap-2">
                <Input
                  type="text"
                  placeholder="BTC"
                  value={baseSymbol}
                  onChange={(e) => setBaseSymbol(e.target.value.toUpperCase())}
                  className="w-24"
                />
                <span className="text-muted-foreground">/</span>
                <Input
                  type="text"
                  placeholder="USDT"
                  value={quoteSymbol}
                  onChange={(e) => setQuoteSymbol(e.target.value.toUpperCase())}
                  className="w-24"
                />
              </div>
            </div>

            <TimeInput
              defaultTimeframe={timeframe}
              onTimeframeChange={setTimeframe}
              onStartTimestampChange={setStartTimestamp}
              onEndTimestampChange={setEndTimestamp}
            />
          </CardContent>
        </Card>

        {/* Feature Engineering Card */}
        <Card>
          <CardHeader>
            <CardTitle>Dataset Preparation</CardTitle>
            <CardDescription>Select technical indicators and configure feature parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Label>Technical Indicators (Select All)</Label>
                <Checkbox
                  id="select-all"
                  checked={indicators.length === AVAILABLE_INDICATORS.length}
                  onCheckedChange={(checked) => handleSelectAllIndicators(checked === true)}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {AVAILABLE_INDICATORS.map((indicator) => (
                  <div key={indicator.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={indicator.id}
                      checked={indicators.includes(indicator.id)}
                      onCheckedChange={(checked) => handleIndicatorChange(indicator.id, checked === true)}
                    />
                    <Label htmlFor={indicator.id}>{indicator.label}</Label>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <Label htmlFor="look-back">Look Back Period</Label>
              <Input
                id="look-back"
                type="number"
                value={lookBack}
                onChange={(e) => setLookBack(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">Number of past periods to use as input for prediction</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="prediction-horizon">Prediction Horizon</Label>
              <Input
                id="prediction-horizon"
                type="number"
                value={predictionHorizon}
                onChange={(e) => setPredictionHorizon(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">Number of future periods to predict</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="price-change-threshold">Price Change Threshold (%)</Label>
              <Input
                id="price-change-threshold"
                type="number"
                value={priceChangeThreshold}
                onChange={(e) => setPriceChangeThreshold(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">Minimum price change to consider as a valid signal</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="window-size">Training Window Size</Label>
              <Input
                id="window-size"
                type="number"
                value={windowSize}
                onChange={(e) => setWindowSize(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">
                Number of periods to use for training the model
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="retrain-interval">Retrain Interval</Label>
              <Input
                id="retrain-interval"
                type="number"
                value={retrainInterval}
                onChange={(e) => setRetrainInterval(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">
                Number of periods between model retraining (e.g., 168 hours = 1 week for 1h timeframe)
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Model Configuration Card */}
        <Card>
          <CardHeader>
            <CardTitle>Model Configuration</CardTitle>
            <CardDescription>Select and configure the machine learning model</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="model-name">Model</Label>
              <Select value={modelName} onValueChange={handleModelChange}>
                <SelectTrigger id="model-name">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {models.map((model) => (
                    <SelectItem key={model.name} value={model.name}>
                      {model.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {modelName && (
              <div className="space-y-2">
                <Label>Model Parameters</Label>
                <Textarea
                  value={modelParams}
                  onChange={(e) => handleModelParamsChange(e.target.value)}
                  className="font-mono text-sm"
                  rows={10}
                />
                <p className="text-sm text-muted-foreground">
                  Edit model parameters (JSON format)
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Trading Parameters Card */}
        <Card>
          <CardHeader>
            <CardTitle>Trading Parameters</CardTitle>
            <CardDescription>Configure trading strategy parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="buy-threshold">Buy Threshold: {buyThreshold}%</Label>
              <div className="flex items-center space-x-4">
                <span>50%</span>
                <Slider
                  id="buy-threshold"
                  min={50}
                  max={100}
                  step={5}
                  value={[buyThreshold]}
                  onValueChange={(value) => setBuyThreshold(value[0])}
                />
                <span>95%</span>
              </div>
              <p className="text-sm text-muted-foreground">Minimum prediction probability to trigger a buy signal</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="sell-threshold">Sell Threshold: {sellThreshold}%</Label>
              <div className="flex items-center space-x-4">
                <span>30%</span>
                <Slider
                  id="sell-threshold"
                  min={0}
                  max={100}
                  step={5}
                  value={[sellThreshold]}
                  onValueChange={(value) => setSellThreshold(value[0])}
                />
                <span>80%</span>
              </div>
              <p className="text-sm text-muted-foreground">Minimum prediction probability to trigger a sell signal</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="stop-loss">Stop Loss (%)</Label>
              <Input
                id="stop-loss"
                type="number"
                value={stopLossPct}
                onChange={(e) => setStopLossPct(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">
                Percentage drop from entry price that triggers a stop loss
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="transaction-fee">Transaction Fee (%)</Label>
              <Input
                id="transaction-fee"
                type="number"
                min={0}
                max={5}
                step={0.01}
                value={transactionFee}
                onChange={(e) => setTransactionFee(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">Percentage of transaction fee (e.g. 0.1%). Refer to the exchange for the actual fee.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="slippage">Slippage (%)</Label>
              <Input
                id="slippage"
                type="number"
                min={0}
                max={5}
                step={0.01}
                value={slippage}
                onChange={(e) => setSlippage(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">Expected slippage percentage for trades</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="risk-free-rate">Risk Free Rate (%)</Label>
              <Input
                id="risk-free-rate"
                type="number"
                min={0}
                max={10}
                step={0.1}
                value={riskFreeRate}
                onChange={(e) => setRiskFreeRate(Number(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">Annual risk-free rate for calculating Sharpe ratio</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="initial-balance">Initial Balance (Quote Currency, e.g. USDT)</Label>
              <Input
                id="initial-balance"
                type="number"
                min={100}
                value={initialBalance}
                onChange={(e) => setInitialBalance(Number(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-position-size">Maximum Position Size (Optional)</Label>
              <Input
                id="max-position-size"
                type="number"
                min={0}
                value={maxPositionSize || ''}
                onChange={(e) => setMaxPositionSize(e.target.value ? Number(e.target.value) : null)}
                placeholder="Leave empty for no limit"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="min-position-size">Minimum Position Size (Optional)</Label>
              <Input
                id="min-position-size"
                type="number"
                min={0}
                value={minPositionSize || ''}
                onChange={(e) => setMinPositionSize(e.target.value ? Number(e.target.value) : null)}
                placeholder="Leave empty for no limit"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6">
        <Button onClick={handleRunBacktest} disabled={isLoading} className="w-full">
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running Backtest...
            </>
          ) : (
            "Run Backtest"
          )}
        </Button>
      </div>
    </div>
  )
}
