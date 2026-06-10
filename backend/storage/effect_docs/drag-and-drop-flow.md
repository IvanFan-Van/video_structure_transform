# DragAndDropFlow

## Description

Simulates dragging a file into a drop zone, then a progress bar fills. A micro-interaction composition: a file icon is dragged across the frame into a dashed dropzone. The dropzone border highlights via interpolateColors, the file fades, and a progress bar grows from 0 to 100%.

## Installation

```
pnpm dlx shadcn@latest add @remocn/drag-and-drop-flow
```

## Usage

### Basic Usage

"File Upload": Simulate dragging a file into a dropzone for upload. Use for upload flow demos.

```tsx
<DragAndDropFlow accent="#0ea5e9" dropzoneLabel="Drop file to upload" fileName="design.fig" />
```

### Custom Accent

Use a brand color for the drag and progress bar.

```tsx
<DragAndDropFlow
  accent="#7c3aed"
  dropzoneLabel="Drag your file here"
  fileName="export.csv"
  background="#0f172a"
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| accent | string | "#0ea5e9" | Accent for file icon, dropzone highlight, and progress bar. |
| dropzoneLabel | string | "Drop file to upload" | Label inside dropzone. |
| fileName | string | "design.fig" | File name above progress bar. |
| background | string | "#fafafa" | Frame background. |
| className | string | - | Optional className. |

## Notes

- **Three timed phases** — Animation splits durationInFrames into drag (~45%), highlight handoff (~10%), and upload (remainder).
- **Width is intentional** — Progress bar grows by animating width instead of `transform: scaleX` so rounded ends stay crisp.
