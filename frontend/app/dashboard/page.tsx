import Dashboard from "@/components/dashboard"
import { getAvailableData } from "@/lib/api"

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const availableData = await getAvailableData()
  
  return (
    <div className="py-4 md:py-8">
      <Dashboard availableData={availableData} />
    </div>
  )
} 