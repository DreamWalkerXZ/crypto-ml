import Models from "@/components/models"
import { getAvailableModels } from "@/lib/api"

export const dynamic = 'force-dynamic'

export default async function ModelsPage() {
  const availableModels = await getAvailableModels()

  return (
    <div className="py-4 md:py-8">
      <Models availableModels={availableModels} />
    </div>
  )
} 