# Effect Menu

_Work in progress..._

- [Stencil](#stencil)
- [Background](#background)
- [Perspective](#perspective)

## Stencil

The Stencil effect allows you to lock certain colors so that they cannot
be painted over.
This is a simple way of specifying a foreground layer.
Any drawing on the screen goes behind this foreground layer.
When a stencil is active, an inverse `S` appears on the title bar.

### Make...
### Remake
### Lock FG
### Reverse
### On/Off
### Free
## Background

A background allows you to draw over top of an image, but when you erase
the drawing with the right mouse button, the background will reappear under
the drawing.

There are two background modes that are indicated in the title bar:
- `B` - Background
  - If you use the `Fix` menu item, it will create the background from the current image.
  - If you save the image with the background showing, the image and the background will be flattened into a single picture
- `R` - Reference
  - If you use the `Open...` menu item, if will load a reference image, which can be any resolution or color depth and does not effect the image you are editing.
  - If you save the image with the reference image showing, only the image will be saved. Color zero will be saved where the reference image was.

### Fix
### Open...
### On/Off
### Free
## Perspective

