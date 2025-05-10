"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AvailableDataTable } from "@/components/available-data-table"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"
import { AvailableDataResponse } from "@/lib/types"
import { fetchData, getAvailableData } from "@/lib/api"
import TradingViewWidget from "@/components/tradingview-widget"
import { TimeInput } from "@/components/time-input"

export default function DataManagement() {
  const [isLoading, setIsLoading] = useState(false)
  const [baseSymbol, setBaseSymbol] = useState("BTC")
  const [quoteSymbol, setQuoteSymbol] = useState("USDT")
  const [timeframe, setTimeframe] = useState("1h")
  const [startTimestamp, setStartTimestamp] = useState("")
  const [endTimestamp, setEndTimestamp] = useState("")
  const [data, setData] = useState<AvailableDataResponse[]>([])

  const handleFetchData = async () => {
    if (!startTimestamp || !endTimestamp) {
      toast.error("Please select start and end timestamps")
      return
    }

    setIsLoading(true)

    try {
      const response = await fetchData({
        symbol: `${baseSymbol}/${quoteSymbol}`,
        timeframe,
        start_timestamp: startTimestamp,
        end_timestamp: endTimestamp,
      })

      if (response.success) {
        toast.success(`Successfully fetched ${timeframe} data for ${baseSymbol}/${quoteSymbol}`)
        // Refresh available data list
        const availableDataResponse = await getAvailableData()
        if (availableDataResponse.success) {
          setData(availableDataResponse.data)
        }
      } else {
        toast.error(response.message || "Failed to fetch data")
      }
    } catch (error) {
      toast.error("Error fetching data. Please try again")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Fetch Market Data</CardTitle>
          <CardDescription>Fetch cryptocurrency market data from exchange</CardDescription>
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
        <CardFooter>
          <Button onClick={handleFetchData} disabled={isLoading} className="w-full">
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Fetching Data...
              </>
            ) : (
              "Fetch Data"
            )}
          </Button>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Available Data</CardTitle>
          <CardDescription>Data ranges available in the database</CardDescription>
        </CardHeader>
        <CardContent>
          <AvailableDataTable data={data} onDataChange={setData} />
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Market Chart</CardTitle>
          <CardDescription>Real-time market data visualization</CardDescription>
        </CardHeader>
        <CardContent className="h-[600px]">
          <TradingViewWidget />
        </CardContent>
      </Card>
    </div>
  )
}
