"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ModelInfo } from "@/lib/types"

interface ModelsProps {
  availableModels: {
    success: boolean;
    data: ModelInfo[];
    message?: string;
  };
}

export default function Models({ availableModels }: ModelsProps) {
  const models = availableModels.data || [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Available Models</CardTitle>
          <CardDescription>Machine learning models available for price direction prediction</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {models.map((model) => (
              <Card key={model.name}>
                <CardHeader>
                  <CardTitle>{model.name}</CardTitle>
                  <CardDescription>{model.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Default Parameters:</h4>
                    <div className="bg-muted p-2 rounded-md">
                      <pre className="text-xs overflow-auto">{JSON.stringify(model.default_params, null, 2)}</pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
