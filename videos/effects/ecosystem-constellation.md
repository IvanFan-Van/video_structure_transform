# EcosystemConstellation

## Description

A central product logo orbited by integration satellites with pulsing data lines. A composition for telling an "everything connects" story. A pulsing logo sits in the center while integration satellites fly in and settle into elliptical orbits at different radii and angular speeds. Connection lines between the hub and each satellite periodically light up.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/ecosystem-constellation
```

## Usage

### Basic Usage

A hub logo with orbiting satellites. Use for showing product integrations.

```tsx
<EcosystemConstellation satelliteCount={6} centerLabel="V" accentColor="#a855f7" />
```

### Fewer Satellites

A simpler constellation with 3 satellites for a cleaner look.

```tsx
<EcosystemConstellation satelliteCount={3} centerLabel="R" accentColor="#22c55e" />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| satelliteCount | `number` | `6` | Number of orbiting satellites (3..8). |
| centerLabel | `string` | `"V"` | Label inside the central hub. |
| accentColor | `string` | `"#a855f7"` | Hub, glow, and connection line color. |
| className | `string` | — | Optional className. |

## Notes

Orbits are elliptical, not circular — Each satellite uses different radiusX and radiusY plus its own angular speed, so the constellation never falls into a robotic symmetric pattern.
