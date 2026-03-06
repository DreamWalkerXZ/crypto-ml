# Crypto ML Frontend

Modern web application for cryptocurrency trading strategy backtesting, built with Next.js 15, TypeScript, and shadcn/ui.

## Features

- **Dashboard**: Overview of recent backtests and available data
- **Data Management**: Fetch and manage market data from Binance
- **Model Browser**: Browse available ML models with detailed information
- **Backtest Configuration**: Configure and run backtests with intuitive forms
- **Results Analysis**: View detailed metrics, equity curves, and trade logs

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (Radix UI primitives)
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod validation
- **Icons**: Lucide React

## Prerequisites

- Node.js 18+
- npm or pnpm

## Installation

```bash
# Install dependencies
npm install

# or with pnpm
pnpm install
```

## Development

```bash
# Start development server
npm run dev

# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build

```bash
# Production build
npm run build

# Start production server
npm run start
```

## Linting

```bash
# Run ESLint
npm run lint
```

## Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

## Project Structure

```text
frontend/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Dashboard home
│   ├── data/                # Data management
│   ├── models/              # Model information
│   ├── backtest/            # Backtest configuration
│   └── results/             # Backtest results
├── components/               # React components
│   ├── *.tsx                # Feature components
│   └── ui/                  # shadcn/ui components
├── hooks/                    # Custom React hooks
├── lib/                      # Utilities
│   ├── api.ts               # API client
│   ├── types.ts             # TypeScript types
│   └── utils.ts             # Utility functions
├── styles/                   # Global styles
├── public/                   # Static assets
├── next.config.mjs          # Next.js configuration
├── tailwind.config.ts       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
└── components.json          # shadcn/ui configuration
```

## Pages

### Dashboard (`/`)

Overview of trading activities with:

- Recent backtests summary
- Available data ranges
- Quick navigation

### Data (`/data`)

Fetch and manage market data:

- Select trading pair, timeframe, and date range
- View available data summary
- Automatic duplicate detection

### Models (`/models`)

Browse available ML models:

- Model descriptions and parameters
- Feature requirements
- Default configurations

### Backtest (`/backtest`)

Configure and run backtests:

- Model selection
- Technical indicators
- Trading parameters (thresholds, stop loss, fees)
- Real-time progress tracking

### Results (`/results`)

View backtest results:

- Performance metrics table
- Equity curve visualization
- Detailed trade logs
- Parameter comparison

## Adding New Components

Use shadcn/ui CLI to add new components:

```bash
npx shadcn-ui@latest add [component-name]
```

Or manually create components in `components/`:

```tsx
import { cn } from "@/lib/utils"

interface MyComponentProps {
  className?: string
  // ... other props
}

export function MyComponent({ className }: MyComponentProps) {
  return (
    <div className={cn("base-styles", className)}>
      {/* content */}
    </div>
  )
}
```

## API Client

The API client (`lib/api.ts`) provides typed functions for backend communication:

```typescript
import { fetchData, runBacktest, getBacktestResult } from '@/lib/api'

// Fetch market data
const result = await fetchData({
  symbol: 'BTC/USDT',
  timeframe: '1h',
  start_timestamp: '2024-01-01T00:00:00Z',
  end_timestamp: '2024-12-31T23:59:59Z'
})

// Run backtest
const backtest = await runBacktest(params)

// Get results
const result = await getBacktestResult(backtestId)
```

## Type Safety

TypeScript types are defined in `lib/types.ts` and must be kept in sync with backend Pydantic schemas:

```typescript
export interface BacktestParams {
  symbol: string
  timeframe: string
  // ... other fields
}

export interface BacktestResult {
  id: string
  params: BacktestParams
  results: BacktestMetrics
}
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [COPYING](../COPYING) file for details.
