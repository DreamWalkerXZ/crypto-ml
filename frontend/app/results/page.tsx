import { BacktestResultsTable } from "@/components/backtest-results-table"
import { listBacktestResults } from "@/lib/api"

export const dynamic = 'force-dynamic'

export default async function ResultsPage() {
  const backtestResults = await listBacktestResults()

  return (
    <div className="py-4 md:py-8">
      <BacktestResultsTable backtestResults={backtestResults.data || []} />
    </div>
  )
} 