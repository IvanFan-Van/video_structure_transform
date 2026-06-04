# bounding-box-selector

## Description

Figma-style selection rectangle appears around any element. Wraps children in a relatively positioned container and overlays an absolutely positioned selection border with eight corner and edge handles. The border fades in and slightly scales up via spring() at the configured frame.

## Installation

pnpm dlx shadcn@latest add @remocn/bounding-box-selector

## Usage

### Basic Usage

A bounding box appears around a UI element. Use for tutorial-style "look here" moments.

```
<BoundingBoxSelector borderColor="#0ea5e9" appearAt={30}>
  <YourElement />
</BoundingBoxSelector>
```

### Multi-step Tutorial

Use multiple selectors with different appearAt frames for step-by-step tutorials.

```
<BoundingBoxSelector borderColor="#ff5e3a" handleColor="#ff5e3a" borderWidth={3} appearAt={60}>
  <StepTwo />
</BoundingBoxSelector>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| children | ReactNode | - | The element to wrap. Falls back to a placeholder rectangle. |
| borderColor | string | #0ea5e9 | Color of the selection border. |
| handleColor | string | #0ea5e9 | Stroke color of the corner/edge handles. |
| borderWidth | number | 2 | Border width in pixels. |
| appearAt | number | 15 | Frame at which the selection box appears. |
| background | string | #fafafa | Outer background color. |
| className | string | - | Optional className. |

## Notes

Sizing — This component reads its size from the wrapped child via display: inline-block. If you need pixel-perfect placement around dynamic content, pass children with explicit width/height.
