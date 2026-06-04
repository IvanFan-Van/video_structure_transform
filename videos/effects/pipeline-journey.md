# PipelineJourney

## Description

A Kanban ticket flies between columns, triggering events along the way. The card lifts out of Todo, arcs through the air with a tilt and growing shadow, lands in In Progress where a brief timer ticks, then takes off again toward Done — where it triggers a deterministic confetti burst on touchdown.

## Installation

```
pnpm dlx shadcn@latest add @remocn/pipeline-journey
```

## Usage

### Kanban Flow

A ticket moves through a pipeline with confetti at the end. Use for workflow/productivity tool demos.

```tsx
<PipelineJourney cardLabel="Build pipeline" accentColor="#22c55e" />
```

### Custom Ticket

Change the ticket label and accent for a different workflow.

```tsx
<PipelineJourney cardLabel="Review PR" accentColor="#7c3aed" speed={1.5} />
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| cardLabel | string | "Build pipeline" | Title on the flying ticket. |
| accentColor | string | "#22c55e" | Ticket border, status dot and confetti color. |
| speed | number | 1 | Multiplier for current frame. |
| className | string | — | Optional className. |

## Notes

Determinism beats Math.random — The confetti burst uses deterministic hashing so every render produces an identical frame. Never reach for Math.random inside a Remotion component.
