"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface TimeInputProps {
  onTimeframeChange: (value: string) => void
  onStartTimestampChange: (value: string) => void
  onEndTimestampChange: (value: string) => void
  defaultTimeframe?: string
}

export function TimeInput({
  onTimeframeChange,
  onStartTimestampChange,
  onEndTimestampChange,
  defaultTimeframe = "1h"
}: TimeInputProps) {
  const [timeframe, setTimeframe] = useState(defaultTimeframe)
  const [startDate, setStartDate] = useState({
    year: "",
    month: "",
    day: "",
    hour: "",
    minute: "",
  })
  const [endDate, setEndDate] = useState({
    year: "",
    month: "",
    day: "",
    hour: "",
    minute: "",
  })

  const handleDateChange = (
    date: typeof startDate,
    setDate: (date: typeof startDate) => void,
    field: keyof typeof startDate,
    value: string,
    nextField?: keyof typeof startDate,
    isStart: boolean = true
  ) => {
    const newDate = { ...date, [field]: value }
    setDate(newDate)
    
    // Update corresponding timestamp
    if (Object.values(newDate).every(v => v)) {
      const timestamp = `${newDate.year}-${newDate.month}-${newDate.day}T${newDate.hour}:${newDate.minute}:00`
      if (isStart) {
        onStartTimestampChange(timestamp)
      } else {
        onEndTimestampChange(timestamp)
      }
    }

    // If input reaches max length and has next field, auto focus
    if (value.length === (field === 'year' ? 4 : 2) && nextField) {
      const prefix = isStart ? 'start-' : 'end-'
      const nextInput = document.querySelector(`input[name="${prefix}${nextField}"]`) as HTMLInputElement
      if (nextInput) {
        nextInput.focus()
      }
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="timeframe">Timeframe</Label>
        <Select value={timeframe} onValueChange={(value) => {
          setTimeframe(value)
          onTimeframeChange(value)
        }}>
          <SelectTrigger id="timeframe">
            <SelectValue placeholder="Select timeframe" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1m">1 minute</SelectItem>
            <SelectItem value="5m">5 minutes</SelectItem>
            <SelectItem value="15m">15 minutes</SelectItem>
            <SelectItem value="30m">30 minutes</SelectItem>
            <SelectItem value="1h">1 hour</SelectItem>
            <SelectItem value="3h">3 hours</SelectItem>
            <SelectItem value="6h">6 hours</SelectItem>
            <SelectItem value="12h">12 hours</SelectItem>
            <SelectItem value="1d">1 day</SelectItem>
            <SelectItem value="3d">3 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Start Timestamp</Label>
        <div className="flex items-center gap-1">
          <Input
            type="text"
            name="start-year"
            placeholder="YYYY"
            maxLength={4}
            value={startDate.year}
            onChange={(e) => handleDateChange(startDate, setStartDate, "year", e.target.value, "month", true)}
            className="w-20"
          />
          <span className="text-muted-foreground">-</span>
          <Input
            type="text"
            name="start-month"
            placeholder="MM"
            maxLength={2}
            value={startDate.month}
            onChange={(e) => handleDateChange(startDate, setStartDate, "month", e.target.value, "day", true)}
            className="w-16"
          />
          <span className="text-muted-foreground">-</span>
          <Input
            type="text"
            name="start-day"
            placeholder="DD"
            maxLength={2}
            value={startDate.day}
            onChange={(e) => handleDateChange(startDate, setStartDate, "day", e.target.value, "hour", true)}
            className="w-16"
          />
          <span className="text-muted-foreground ml-2"> </span>
          <Input
            type="text"
            name="start-hour"
            placeholder="HH"
            maxLength={2}
            value={startDate.hour}
            onChange={(e) => handleDateChange(startDate, setStartDate, "hour", e.target.value, "minute", true)}
            className="w-16"
          />
          <span className="text-muted-foreground">:</span>
          <Input
            type="text"
            name="start-minute"
            placeholder="MM"
            maxLength={2}
            value={startDate.minute}
            onChange={(e) => handleDateChange(startDate, setStartDate, "minute", e.target.value, undefined, true)}
            className="w-16"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>End Timestamp</Label>
        <div className="flex items-center gap-1">
          <Input
            type="text"
            name="end-year"
            placeholder="YYYY"
            maxLength={4}
            value={endDate.year}
            onChange={(e) => handleDateChange(endDate, setEndDate, "year", e.target.value, "month", false)}
            className="w-20"
          />
          <span className="text-muted-foreground">-</span>
          <Input
            type="text"
            name="end-month"
            placeholder="MM"
            maxLength={2}
            value={endDate.month}
            onChange={(e) => handleDateChange(endDate, setEndDate, "month", e.target.value, "day", false)}
            className="w-16"
          />
          <span className="text-muted-foreground">-</span>
          <Input
            type="text"
            name="end-day"
            placeholder="DD"
            maxLength={2}
            value={endDate.day}
            onChange={(e) => handleDateChange(endDate, setEndDate, "day", e.target.value, "hour", false)}
            className="w-16"
          />
          <span className="text-muted-foreground ml-2"> </span>
          <Input
            type="text"
            name="end-hour"
            placeholder="HH"
            maxLength={2}
            value={endDate.hour}
            onChange={(e) => handleDateChange(endDate, setEndDate, "hour", e.target.value, "minute", false)}
            className="w-16"
          />
          <span className="text-muted-foreground">:</span>
          <Input
            type="text"
            name="end-minute"
            placeholder="MM"
            maxLength={2}
            value={endDate.minute}
            onChange={(e) => handleDateChange(endDate, setEndDate, "minute", e.target.value, undefined, false)}
            className="w-16"
          />
        </div>
      </div>
    </div>
  )
} 