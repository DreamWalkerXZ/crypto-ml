"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
  Cell,
  Brush,
} from "recharts"
import { getBacktestResult, getOhlcvData } from "@/lib/api"
import { BacktestResult } from "@/lib/types"
import { formatDate } from "@/lib/utils"

export default function BacktestDetailPage() {
  const params = useParams()
  const backtestId = params.id as string
  const [backtestDetail, setBacktestDetail] = useState<BacktestResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [buyAndHoldData, setBuyAndHoldData] = useState<any[]>([])
  const router = useRouter()

  useEffect(() => {
    const fetchBacktestDetail = async () => {
      setIsLoading(true)
      try {
        const response = await getBacktestResult(backtestId)
        if (response.success && response.data) {
          const backtestData = response.data
          setBacktestDetail(backtestData)
          
          // Get buy and hold strategy data
          const ohlcvResponse = await getOhlcvData(
            backtestData.params.symbol,
            backtestData.params.timeframe,
            backtestData.params.start_timestamp,
            backtestData.params.end_timestamp
          )
          
          if (ohlcvResponse.success && ohlcvResponse.data) {
            // Calculate buy and hold strategy equity curve
            const initialPrice = ohlcvResponse.data[0].close
            const buyAndHoldCurve = ohlcvResponse.data.map((item: any) => ({
              time: item.timestamp,
              value: (item.close / initialPrice) * backtestData.params.initial_balance
            }))
            setBuyAndHoldData(buyAndHoldCurve)
          }
        } else {
          console.error("Failed to fetch backtest detail:", response.message)
        }
      } catch (error) {
        console.error("Failed to fetch backtest detail:", error)
      } finally {
        setIsLoading(false)
      }
    }

    if (backtestId) {
      fetchBacktestDetail()
    }
  }, [backtestId])

  const handleGoBack = () => {
    router.back()
  }

  if (isLoading) {
    return <div className="flex justify-center p-8">Loading backtest details...</div>
  }

  if (!backtestDetail) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <p className="text-lg mb-4">Backtest result not found</p>
        <Button onClick={handleGoBack}>Back</Button>
      </div>
    )
  }

  return (
    <div className="py-4 md:py-8">
      <div className="mb-6">
        <Button variant="outline" size="sm" onClick={handleGoBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Results
        </Button>
      </div>

      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Backtest: {backtestDetail.params.symbol} ({backtestDetail.params.timeframe})
            </h1>
            <p className="text-muted-foreground">
              Model: {backtestDetail.params.model_name} • ID: {backtestId}
            </p>
          </div>
          <Badge
            className="text-lg py-1 px-3 self-start md:self-auto"
            variant={backtestDetail.results.total_return_pct >= 0 ? "success" : "destructive"}
          >
            {backtestDetail.results.total_return_pct >= 0 ? "+" : ""}
            {backtestDetail.results.total_return_pct.toFixed(2)}% Return
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Total Return"
            value={`${backtestDetail.results.total_return_pct.toFixed(2)}%`}
            positive={backtestDetail.results.total_return_pct > 0}
          />
          <MetricCard
            title="Win Rate"
            value={`${backtestDetail.results.win_rate_pct.toFixed(2)}%`}
            positive={backtestDetail.results.win_rate_pct > 50}
          />
          <MetricCard
            title="Max Drawdown"
            value={`${backtestDetail.results.max_drawdown_pct.toFixed(2)}%`}
            positive={false}
          />
          <MetricCard
            title="Sharpe Ratio"
            value={backtestDetail.results.sharpe_ratio.toFixed(2)}
            positive={backtestDetail.results.sharpe_ratio > 1}
          />
        </div>

        <Tabs defaultValue="equity" className="space-y-4">
          <TabsList>
            <TabsTrigger value="equity">Equity Curve</TabsTrigger>
            <TabsTrigger value="trades">Trade Logs</TabsTrigger>
            <TabsTrigger value="parameters">Parameters</TabsTrigger>
            <TabsTrigger value="metrics">Detailed Metrics</TabsTrigger>
          </TabsList>

          <TabsContent value="equity" className="space-y-4">
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={backtestDetail.results.equity_curve}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="time" 
                    tickFormatter={(value) => formatDate(value)}
                    tick={{ fontSize: 12 }} 
                  />
                  <YAxis 
                    domain={[
                      (dataMin: number) => Math.min(dataMin, ...buyAndHoldData.map(d => d.value)) * 0.9,
                      (dataMax: number) => Math.max(dataMax, ...buyAndHoldData.map(d => d.value)) * 1.1
                    ]} 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
                  />
                  <Tooltip
                    formatter={(value: any, name: string) => [`$${Number(value).toLocaleString()}`, name]}
                    labelFormatter={(label) => `Date: ${formatDate(label)}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#3C82F6"
                    strokeWidth={2} 
                    dot={false}
                    activeDot={{ r: 4 }}
                    name="Strategy"
                  />
                  <Line 
                    type="monotone" 
                    data={buyAndHoldData}
                    dataKey="value"
                    stroke="#94A3B8"
                    strokeWidth={1}
                    dot={false}
                    activeDot={{ r: 4 }}
                    name="Buy & Hold"
                  />
                  <Brush
                    dataKey="time"
                    height={30}
                    stroke="#94A3B8"
                    tickFormatter={(value) => formatDate(value)}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>

          <TabsContent value="trades" className="space-y-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Shares</TableHead>
                  <TableHead>Fee</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {backtestDetail.results.trade_logs.map((trade: any, index: number) => (
                  <TableRow key={index}>
                    <TableCell>{formatDate(trade.timestamp)}</TableCell>
                    <TableCell>
                      <Badge variant={trade.type === "buy" ? "success" : "destructive"}>
                        {trade.type === "buy" ? "Buy" : "Sell"}
                      </Badge>
                    </TableCell>
                    <TableCell>${trade.price.toLocaleString()}</TableCell>
                    <TableCell>{trade.shares.toLocaleString()}</TableCell>
                    <TableCell>${trade.fee_cash.toLocaleString()}</TableCell>
                    <TableCell>{trade.reason || "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>

          <TabsContent value="parameters" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-medium text-lg">Data Parameters</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">Symbol:</div>
                      <div>{backtestDetail.params.symbol}</div>
                      <div className="text-muted-foreground">Timeframe:</div>
                      <div>{backtestDetail.params.timeframe}</div>
                      <div className="text-muted-foreground">Start Time:</div>
                      <div>{formatDate(backtestDetail.params.start_timestamp)}</div>
                      <div className="text-muted-foreground">End Time:</div>
                      <div>{formatDate(backtestDetail.params.end_timestamp)}</div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-medium text-lg">Dataset Preparation</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">Lookback:</div>
                      <div>{backtestDetail.params.look_back} periods</div>
                      <div className="text-muted-foreground">Prediction Horizon:</div>
                      <div>{backtestDetail.params.prediction_horizon} periods</div>
                      <div className="text-muted-foreground">Retrain Interval:</div>
                      <div>{backtestDetail.params.retrain_interval} periods</div>
                      <div className="text-muted-foreground">Training Window:</div>
                      <div>{backtestDetail.params.window_size} periods</div>
                    </div>
                    <div className="mt-2">
                      <div className="text-muted-foreground text-sm mb-2">Technical Indicators:</div>
                      <div className="flex flex-wrap gap-1">
                        {backtestDetail.params.ta_indicators.map((indicator: string, index: number) => (
                          <Badge key={index} variant="outline">
                            {indicator}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-medium text-lg">Model Configuration</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">Model Name:</div>
                      <div>{backtestDetail.params.model_name}</div>
                    </div>
                    <div className="mt-2">
                      <div className="text-muted-foreground text-sm mb-2">Model Parameters:</div>
                      <Textarea
                        value={JSON.stringify(backtestDetail.params.model_params || {}, null, 2)}
                        readOnly
                        className="h-[200px] font-mono text-sm"
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-medium text-lg">Trading Parameters</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">Buy Threshold:</div>
                      <div>{(backtestDetail.params.buy_threshold * 100).toFixed(0)}%</div>
                      <div className="text-muted-foreground">Sell Threshold:</div>
                      <div>{(backtestDetail.params.sell_threshold * 100).toFixed(0)}%</div>
                      <div className="text-muted-foreground">Stop Loss:</div>
                      <div>{(backtestDetail.params.stop_loss_pct * 100).toFixed(2)}%</div>
                      <div className="text-muted-foreground">Initial Balance:</div>
                      <div>${backtestDetail.params.initial_balance.toLocaleString()}</div>
                      <div className="text-muted-foreground">Transaction Fee:</div>
                      <div>{(backtestDetail.params.transaction_fee * 100).toFixed(2)}%</div>
                      <div className="text-muted-foreground">Slippage:</div>
                      <div>{(backtestDetail.params.slippage * 100).toFixed(2)}%</div>
                      <div className="text-muted-foreground">Risk Free Rate:</div>
                      <div>{(backtestDetail.params.risk_free_rate * 100).toFixed(2)}%</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="metrics" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium text-lg mb-4">Return Metrics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <MetricCard
                      title="Total Return"
                      value={`${backtestDetail.results.total_return_pct.toFixed(2)}%`}
                      positive={backtestDetail.results.total_return_pct > 0}
                    />
                    <MetricCard
                      title="Annualized Return"
                      value={`${backtestDetail.results.annualized_return_pct.toFixed(2)}%`}
                      positive={backtestDetail.results.annualized_return_pct > 0}
                    />
                    <MetricCard
                      title="Sharpe Ratio"
                      value={backtestDetail.results.sharpe_ratio.toFixed(2)}
                      positive={backtestDetail.results.sharpe_ratio > 1}
                    />
                    <MetricCard
                      title="Sortino Ratio"
                      value={backtestDetail.results.sortino_ratio.toFixed(2)}
                      positive={backtestDetail.results.sortino_ratio > 1}
                    />
                    <MetricCard
                      title="Calmar Ratio"
                      value={backtestDetail.results.calmar_ratio.toFixed(2)}
                      positive={backtestDetail.results.calmar_ratio > 1}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium text-lg mb-4">Risk Metrics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <MetricCard
                      title="Max Drawdown"
                      value={`${backtestDetail.results.max_drawdown_pct.toFixed(2)}%`}
                      positive={false}
                    />
                    <MetricCard
                      title="Max Drawdown Duration"
                      value={`${backtestDetail.results.max_drawdown_duration} periods`}
                      positive={false}
                    />
                    <MetricCard
                      title="Volatility"
                      value={`${backtestDetail.results.volatility_pct.toFixed(2)}%`}
                      positive={false}
                    />
                    <MetricCard
                      title="Consecutive Losses"
                      value={backtestDetail.results.consecutive_losses.toString()}
                      positive={false}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium text-lg mb-4">Trading Metrics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <MetricCard
                      title="Total Trades"
                      value={backtestDetail.results.total_trades.toString()}
                      positive={true}
                    />
                    <MetricCard
                      title="Win Rate"
                      value={`${backtestDetail.results.win_rate_pct.toFixed(2)}%`}
                      positive={backtestDetail.results.win_rate_pct > 50}
                    />
                    <MetricCard
                      title="Profit Factor"
                      value={backtestDetail.results.profit_factor.toFixed(2)}
                      positive={backtestDetail.results.profit_factor > 1}
                    />
                    <MetricCard
                      title="Avg Trade Return"
                      value={`${backtestDetail.results.avg_trade_return_pct.toFixed(2)}%`}
                      positive={backtestDetail.results.avg_trade_return_pct > 0}
                    />
                    <MetricCard
                      title="Avg Winning Trade"
                      value={`${backtestDetail.results.avg_winning_trade_pct.toFixed(2)}%`}
                      positive={true}
                    />
                    <MetricCard
                      title="Avg Losing Trade"
                      value={`${backtestDetail.results.avg_losing_trade_pct.toFixed(2)}%`}
                      positive={false}
                    />
                    <MetricCard
                      title="Total Fees"
                      value={`$${backtestDetail.results.total_fees.toLocaleString()}`}
                      positive={false}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium text-lg mb-4">Position Metrics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <MetricCard
                      title="Avg Holding Period"
                      value={`${backtestDetail.results.avg_holding_period} periods`}
                      positive={true}
                    />
                    <MetricCard
                      title="Max Holding Period"
                      value={`${backtestDetail.results.max_holding_period} periods`}
                      positive={true}
                    />
                    <MetricCard
                      title="Min Holding Period"
                      value={`${backtestDetail.results.min_holding_period} periods`}
                      positive={true}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

function MetricCard({
  title,
  value,
  positive,
}: {
  title: string
  value: string
  positive: boolean
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-col space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p
            className={`text-2xl font-bold ${positive ? "text-green-500" : "text-red-500"}`}
          >
            {value}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
