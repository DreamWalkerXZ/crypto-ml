"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useRouter } from "next/navigation"
import { formatDate } from "@/lib/utils"
import { BacktestListItem } from "@/lib/types"

interface RecentBacktestsProps {
  backtestResults: BacktestListItem[];
}

export function RecentBacktests({ backtestResults }: RecentBacktestsProps) {
  const router = useRouter()

  const handleBacktestClick = (backtestId: string) => {
    router.push(`/results/${backtestId}`)
  }

  // Only show the last 5 results
  const recentResults = [...backtestResults].reverse().slice(0, 5)

  return (
    <div className="space-y-2">
      {recentResults.map((backtest) => (
        <Card
          key={backtest.id}
          className="hover:bg-accent/50 transition-colors cursor-pointer"
          onClick={() => handleBacktestClick(backtest.id)}
        >
          <CardContent className="p-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium">
                  {backtest.symbol} • {formatDate(backtest.start_timestamp)} - {formatDate(backtest.end_timestamp)} • {backtest.timeframe}
                </div>
                <div className="text-sm text-muted-foreground">
                  {backtest.model_name} • Win Rate: {(backtest.win_rate_pct || 0).toFixed(1)}% • Sharpe: {(backtest.sharpe_ratio || 0).toFixed(2)} • Annualized Return: {(backtest.annualized_return_pct || 0).toFixed(2)}%
                </div>
              </div>
              <Badge variant={backtest.total_return_pct >= 0 ? "success" : "destructive"}>
                {backtest.total_return_pct >= 0 ? "+" : ""}
                {(backtest.total_return_pct || 0).toFixed(2)}%
              </Badge>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
