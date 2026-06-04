# HeroDeviceAssemble

## Description

Layered device mockup that snaps together in 3D before the screen wakes up. A laptop (or phone) materializes from floating layers — back lid, chassis, bezel, and display — drifting in from different Z depths and tilted in 3D space. A single spring collapses everything into place, then the screen fades from black to a mock dashboard with a soft shimmer.

## Installation

```bash
pnpm dlx shadcn@latest add @remocn/hero-device-assemble
```

## Usage

### Basic Usage

A laptop assembles in 3D and the screen wakes up. Use for product hero sections.

```tsx
<HeroDeviceAssemble device="laptop" accentColor="#22c55e" assembleStart={0} />
```

### Phone Hero

A phone assembles with a different accent color.

```tsx
<HeroDeviceAssemble device="phone" accentColor="#7c3aed" assembleStart={10} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| device | `"laptop"` \| `"phone"` | `"laptop"` | Mockup form factor. |
| accentColor | `string` | `"#22c55e"` | Brand accent for in-screen UI highlights. |
| assembleStart | `number` | `0` | Frame assembly spring kicks off. |
| className | `string` | — | Optional className. |

## Notes

The screen stays dark until layers settle — The display is rendered black until the spring resolves, then the mock UI fades in with a diagonal shimmer. That delayed wake-up sells the illusion of a physical device powering on.
