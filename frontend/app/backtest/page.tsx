import BacktestConfiguration from "@/components/backtest-configuration"
import { getAvailableData, getAvailableModels } from "@/lib/api"

export const dynamic = 'force-dynamic'

export default async function BacktestPage() {
  const [availableData, availableModels] = await Promise.all([
    getAvailableData(),
    getAvailableModels(),
  ])

  return (
    <div className="py-4 md:py-8">
      <BacktestConfiguration 
        availableData={availableData.data || []} 
        availableModels={availableModels} 
      />
    </div>
  )
} 