# Spacing options

- [N Total](#n-total)
- [Every Nth dot](#every-nth-dot)
- [Airbrush](#airbrush)
- [Continuous](#continuous)

| ![Spacing](spacing.png) |
| :-----: |
|*Spacing options. These options make more sense with a custom brush, otherwise it just looks like dotted lines. **Continuous** is default drawing mode.* |

## N Total

Defines the total number of times the current brush will be copied along the path. For example, if you draw a circle with a **total spacing** of 14 with a star-shaped brush, this will make a round of 14 stars.

| ![](14stars.png) |
| :-----: |
| *Combined with the [Cycle](../../menus/src/mode.md#cycle) mode using a color range, gives this kind of effect.* |

*Note: With shapes that have multiple line segments like rectangles and polygons, the N Total property is applied to each line segment.*

## Every Nth dot

Defines the regular pixel spacing between each time the current brush will be copied along the path. This spacing remains the same whatever the length of the line, the size of the rectangle and so on.

*Note: The default spacing of 8 pixels can be covered by brushes larger than 8 pixels.*

## Airbrush

Airbrush paints using the airbrush tool along the path defined by any tool affected by the Spacing requester. The number '16' sets the number of airbrush sprays to be applied at each pixel along the path. We recommend lowering it to 6 to 8 to better understand the effect. This creates a fuzzy line or shape. You can use this feature with the painting modes from the [Mode](../../menus/src/mode.md) menu to create interesting
effects. For example, using Smooth, Smear, Tint or Cycle with the Airbrush spacing can create interesting textured effects.

![](airbrush-spacing.png)

## Continuous

Default operation. Brush paints continuously without spacing.

---

From left to right, examples of the 4 default settings, with Circle, Rectangle and Line tools, each with a different brush (indicated in red).

![](Spacing-examples.png)

###### Documentation written by Stephane Anquetil
