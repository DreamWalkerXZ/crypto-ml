import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { RecentBacktests } from "@/components/recent-backtests"
import { AvailableDataSummary } from "@/components/available-data-summary"
import { AvailableDataResponse, ModelInfo } from "@/lib/types"
import { getAvailableModels, listBacktestResults } from "@/lib/api"

interface DashboardProps {
  availableData: {
    success: boolean;
    data: AvailableDataResponse[];
    message?: string;
  };
}

export default async function Dashboard({ availableData }: DashboardProps) {
  const [availableModels, backtestResults] = await Promise.all([
    getAvailableModels(),
    listBacktestResults(),
  ])

  // Get unique trading pair count
  const uniqueSymbols = new Set(availableData.data.map(data => data.symbol)).size

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
      <div className="col-span-3 grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Platform Summary</CardTitle>
            <CardDescription>Overview of available data and models</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Available Symbols</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{uniqueSymbols}</div>
                    <p className="text-xs text-muted-foreground">
                      {Array.from(new Set(availableData.data.map(data => data.symbol))).slice(0, 3).join(', ') + (Array.from(new Set(availableData.data.map(data => data.symbol))).length > 3 ? '...' : '')}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Available Models</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{availableModels.data?.length || 0}</div>
                    <p className="text-xs text-muted-foreground">
                      {availableModels.data?.map((model: ModelInfo) => model.name).slice(0, 3).join(', ') + (availableModels.data?.length > 3 ? '...' : '')}
                    </p>
                  </CardContent>
                </Card>
              </div>
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Available Data</CardTitle>
                </CardHeader>
                <CardContent>
                  <AvailableDataSummary availableData={availableData.data} />
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      </div>
      <Card className="col-span-4">
        <CardHeader>
          <CardTitle>Recent Backtests</CardTitle>
          <CardDescription>Latest backtest results and performance</CardDescription>
        </CardHeader>
        <CardContent className="pl-2">
          <RecentBacktests backtestResults={backtestResults.data || []} />
        </CardContent>
      </Card>
    </div>
  )
}
