"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useEffect, useState } from "react"
import { getAvailableData } from "@/lib/api"
import { AvailableDataResponse } from "@/lib/types"
import { formatDate } from "@/lib/utils"

interface AvailableDataTableProps {
  data: AvailableDataResponse[];
  onDataChange: (data: AvailableDataResponse[]) => void;
}

export function AvailableDataTable({ data, onDataChange }: AvailableDataTableProps) {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        const response = await getAvailableData()
        if (response.success && response.data) {
          onDataChange(response.data)
        } else {
          console.error("Failed to fetch data:", response.message)
        }
      } catch (error) {
        console.error("Error occurred while fetching data:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [onDataChange])

  if (isLoading) {
    return <div className="flex justify-center p-4">Loading available data...</div>
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Symbol</TableHead>
          <TableHead>Timeframe</TableHead>
          <TableHead>Start Timestamp</TableHead>
          <TableHead>End Timestamp</TableHead>
          <TableHead className="text-right">Data Points</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((item, index) => (
          <TableRow key={index}>
            <TableCell className="font-medium">{item.symbol}</TableCell>
            <TableCell>{item.timeframe}</TableCell>
            <TableCell>{formatDate(item.start_timestamp)}</TableCell>
            <TableCell>{formatDate(item.end_timestamp)}</TableCell>
            <TableCell className="text-right">{item.data_points.toLocaleString()}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
