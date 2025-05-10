import { Card, CardContent } from "@/components/ui/card"
import { AvailableDataResponse } from "@/lib/types"

interface AvailableDataSummaryProps {
  availableData: AvailableDataResponse[];
}

export function AvailableDataSummary({ availableData }: AvailableDataSummaryProps) {
  // Group data by trading pair
  const groupedData = availableData.reduce((acc, item) => {
    if (!acc[item.symbol]) {
      acc[item.symbol] = [];
    }
    acc[item.symbol].push(item.timeframe);
    return acc;
  }, {} as Record<string, string[]>);

  return (
    <div className="space-y-2">
      {Object.entries(groupedData).map(([symbol, timeframes]) => (
        <Card key={symbol}>
          <CardContent className="p-4">
            <div className="flex justify-between items-center">
              <span className="font-medium">{symbol}</span>
              <div className="flex flex-wrap gap-1">
                {timeframes.map((tf, i) => (
                  <span key={i} className="px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-xs">
                    {tf}
                  </span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
