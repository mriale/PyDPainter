# Fill Type

- [Fill Type](#fill-type)
  - [Solid](#solid)
  - [Brush](#brush)
  - [Wrap](#wrap)
  - [Pattern](#pattern)
  - [AntiAlias \& Smooth](#antialias--smooth)
  - [Gradient](#gradient)
      - [Circular](#circular-fill)
      - [Vertical Line](#vertical-line)
      - [Linear Fill](#linear-fill)
      - [Horizontal Line](#horizontal-line)
      - [Vertical and Horizontal](#vertical-and-horizontal-fill)
  - [Dither](#dither)
    - [No dithering](#no-dithering)
    - [Gradient direction](#gradient-direction)
    - [Random](#random)
    - [Check](#check)
    - [2x2](#2x2)
    - [4x4](#4x4)
    - [8x8](#8x8)
    - [HalfTone](#halftone)
    - [Vertical Bar](#vertbar)
    - [Horizontal Bar](#horizbar)


Right-clicking the **Fill tool** <img src="t-fill.png" width="32"> or the lower-right half of most drawing tools displays this **Fill Type** requester: 

<img src="fill-type.png" width="500">

The options in the requester are explained in the following paragraphs.
When you return to the painting screen after choosing a fill type :
- the current **Gradient** and its orientation,
- current brush fill, if **Pattern** or **Wrap** are selected
- **AntiAlias** or **Smooth** (**AA** or **SM**) type if choosen
are shown in the Color Fill box in the menu bar:

| ![](fill-status.png) |
| :----: |
| *Bar fill status examples.* |

## Solid

**Solid** fills with the current color with no added effects. If you paint or fill your shape using the left button, the shape is filled with the foreground color. If you paint or fill your shape using the right mouse button, it is filled with the background color.

## Brush

**Brush** fills with the current custom brush and sizes it to fit the filled area.


| <img src="fill-brush-ex.png" width="500"> |
| :----: |
| *Three examples of defined brush are on the very left : checkerboard, vertical lines, A letter. Examples of fills in a variety of shapes, from rectangles on the left, to polygons on the right, to circles and inclined ellipses.* |

## Wrap
**Wrap** fills with the current custom brush and adjusts it to the horizontal and vertical shape of the filled area. This gives the illusion of wrapping the brush around a 3D solid. The effect is most pronounced if you use it to fill a shape that is very different from the shape of the custom brush.

*See the comparative examples below.*

## Pattern
**Pattern** fills with a pattern made from current custom brush. It's a "wallpaper" type of filling. There's no stretching, no distortion. It's the patterned fill of early monochrome drawing software.

| <img src="brush-warp-pattern-fill.jpg" width="600"> |
| :----: |
| ***Brush*** *respects the original image of the brush.* ***Warp*** *gives interesting effects on rounded shapes. There are no predefined rules: it's up to you to experiment! You can try yourself loading this example file in: `iff_pics/fill-wrap-comp-ex.iff`* |

## AntiAlias & Smooth

The following two modes are new to **PydPainter**:
* **Smooth** allows you to use the drawing mode of the same name (that of the F8 key) with fill tools. It's a brutal softening, which can give interesting  effects (blur, textures).
* **AntiAliasing** is a more modern mode, which really smoothes the sharp borders of pixels. It's perfect for lettering, diagonal lines or softening the contrast.

*Note that you need an existing design to have a visible effect.*

| ![](AA-ex1.png) ![](AA-ex2.png) |
| :----: |
| *Some AntiAliasing and Smooth examples. **Original** here, can be quickly redone with the Airbrush, or 5-point random brush in various colors.* |

Note that with a limited palette of 16 or less, the performance of these two modes will depend on the color values available in the palette.
If you're smoothing red on a black background, but no dark red/brown color is available, PyDPainter will do its best by using purple and dark grays. Under no circumstances will it alter the palette for you. 

## Gradient

**Gradient** Fills offer a host of creative uses. Their rendering will depend as much on the colors range chosen in the [palette](../../menus/src/palette.md), the shapes drawn, as on the options selected here.

| ![](fill-ex.png) |
| :----: |
| *Examples with a suite of 6 colors (3 bright yellow, cyan, blue and 3 white), a 7-color orange gradient and the default grayscale (12 colors).* |

**Remember to select one of the [Range](../../menus/src/palette.md#range) colors as foreground color to select your gradient and get this type of preview. IE: any grey or the yellow in default screen.**

Select one of the gradient options by clicking it with the left mouse button. Preview will update automatically. 

<img src="gradient-fill-v.png" width="500">


### Circular fill
**Circular fill** paints the gradient as concentric circles, from center to borders with an even distribution without regard to the shape of the object.


 
### Vertical Line
**Vertical Line** fill paints the gradient top-to-bottom adjusting the gradient so that it follows the contours of the shape being filled.

### Linear Fill
**Linear fill** paints the gradient in a line, according to the angle defined, with an even distribution without regard to the shape of the object.

### Horizontal Line
**Horizontal Line** fill paints the gradient left-to-right adjusting the gradient so that it follows the contours of the shape being filled.

### Vertical and Horizontal Fill 
**Vertical and Horizontal** fill paints the gradient from the inside out adjusting the gradient so that it follows the contours of the shape being filled.

*The preview uses the shape of a circle, but remember that the fill tools can fill the whole screen and any type of shape.*

## Gradient direction
**New in PydPainter 2.1.0**: right to the Dither bar, there is an new black arrow that toggles the gradient orientation. Not the gradient up and down direction, but the order of the colors inside a range.
<img src="fill-orientation.png" width="500">
This orientation is first defined by the color order in the **Palette** (`P`). It can now be reversed with a click directly from here. If you have a light to dark blue range in the Palette, and want to use a dark to light blue gradient, just click that arrow.

## Dither

Dithering is the blending of pixels within a **Range** defined in Palette. Usually, it's a gradient, but it doesn't have to be. It can be ordered dithering or a random dithering setting from none to increasingly blended. PyDPainter 2.2.1 introduce a lot of new dithering patterns.

### No dithering

If you don't want to use dithering, set the **Dither** slider to **0**. Pull the **Dither** slider all the way to the left to use this quasi-geometric rasterization. It works with any dithering mode selected from Random to Horizontal bar.

<img src="Dithering-0.png" width="500">

### Random
It's a legacy from Deluxe Paint.
The further the **Dither** slider is pulled to the right, the stronger the blend. Values range from 1 (very light) to 20 (a mishmash of colors).

<img src="Dithering-2.png" width="500">

Dither 2. The beginning of natural randomness.

<img src="Dithering-8.png" width="500">

Dither at 8. More of a mixture, it can be used as a base for coloring rocks or plants.

<img src="Dithering-20.png" width="500">

Max dithering (20). The gradient is barely recognizable. Can be used as a noise base before using other drawing modes such as Smooth or Blend.

### Check

A very basic checkerboard pattern.
### 2x2
A elegant checkerboard pattern with some extra dots.

### 4x4

It's another legacy from Deluxe Paint. If you search for the same pattern as DPaint or previous versions of PyDPainter, use 4x4 with a 13 value. 

<img src="Dithering-on.png" width="500">

### 8x8

The more complex 8x8 pattern. It need some place to draw it's pixels pattern entirely.
### Halftone

A well-know and recognizable pattern from the printing industry. Mey require some place to be nice-looking. Produce nice aquatic effect when stretched out to large Dither value.

### VertBar
May look strange. It's a pattern designed for vertical gradient. So click to Linear Fill and choose a 90° or 270° angle. Of course, you can use it as a creative way with other fill or angle, if you like theses saw shapes. A 2 Dither value produce a basic line alternate which is interesting in any Gradient type.

### HorizBar
May look strange. It's a pattern designed for horizontal gradient, like sky. So click to Linear Fill and choose a 0° or 180° angle. Of course, you can use it in a creative way with other fill or angle, if you like theses saw shapes. A 2 Dither value produce a basic line alternate which is interesting in any Gradient type.

###### Documentation written by Stephane Anquetil
