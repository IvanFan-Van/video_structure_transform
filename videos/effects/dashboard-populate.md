# DashboardPopulate

## Description

An empty dashboard fills itself with data in a cascaded spring sequence. First the structure fades in — tiles, axes, gridlines, legends. Then the data crashes in: KPIs spin up from zero, bars launch from the baseline on staggered springs, the line chart traces itself left to right, and the donut sweeps to its final value.

## Installation

```
pnpm dlx shadcn@latest add @remocn/dashboard-populate
```

## Usage

### Dashboard Reveal

An empty dashboard comes to life with data. Use for analytics product demos.

```tsx
<DashboardPopulate accentColor="#22c55e" kpiTarget={128400} />
```

### Custom KPI

Use a different revenue target and accent.

```tsx
<DashboardPopulate accentColor="#3b82f6" kpiTarget={250000} speed={1.2} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| accentColor | string | "#22c55e" | Color for bars, line, donut and KPI delta. |
| kpiTarget | number | 128400 | Target value the revenue counter animates to. |
| speed | number | 1 | Multiplier for current frame. |
| className | string | — | Optional className. |

## Notes

Structure first, then data — The first 15 frames are reserved for the empty scaffolding so the eye has something to anchor to before the springs hit. Without this beat the populate cascade reads as chaotic.
