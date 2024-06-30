# Fill Type

_needs proofreading by Mark..._


- [Solid](#solid)
- [Brush](#brush)
- [Wrap](#wrap)
- [Pattern](#pattern)
- [Antialias](#antialias--smooth)
- [Smooth](#antialias--smooth)
- [Gradient](#gradient)
- [Dithering](#dither)

Clicking the **Fill tool** ![](t-fill.png) or the right/bottom half of most drawing tools with the right button displays this **Fill Type** requester. 
![](fill-type.png)

The options in the requester are explained in the following paragraphs.
When you return to the painting screen after choosing a fill
type, the current gradient (or pattern, if **Pattern** is se
lected) and its orientation are shown in the Color Fill box in the menu bar
![](fill-status.png)  
*Bar fill status examples.*

## Solid
**Solid** fills with the current color. Flat color alone. If you paint or fill your shape using the left button, the shape is filled with the foreground color. If you paint or fill your shape using the right mouse button, it is filled with the background color.

## Brush

**Brush** fills with the current custom brush and sizes it to fit the filled area.

![](fill-brush-ex.png)  
*The current defined brush is on the left. Examples of fills in a variety of shapes, from rectangles on the left, to polygons on the right, to circles and inclined ellipses.*

## Wrap
**Wrap** fills with the current custom brush and adjusts it to the horizontal and vertical shape of the filled area. This gives the illusion of wrapping the brush around a 3D solid. The effect is most pronounced if you use it to fill a shape that is very different from the shape of the custom brush.  
*See the comparative examples below.*

## Pattern
**Pattern** fills with a pattern made from current custom brush. It's a "wallpaper" type of filling. There's no stretching, no distortion. It's the patterned fill of early monochrome drawing software.

![](brush-warp-pattern-fill.jpg)  
**Brush** *respects the original image of the brush. **Warp** gives interesting effects on rounded shapes. There are no predefined rules: it's up to you to experiment!*


## AntiAlias & Smooth
The following two modes are new to **PydPainter**:  
**Smooth** allows you to use the drawing mode of the same name (that of the F8 key) with fill tools. It's a brutal softening, which can give interesting  effects (blur, textures).
We've added a more modern **AntiAliasing** mode, which really smoothes the sharp borders of pixels. It's perfect for lettering, diagonal lines or softening the contrast.  
*Note that you need an existing design to have a visible effect.* 

![](AA-ex1.png) ![](AA-ex2.png)  
*Some AntiAliasing and Smooth examples. **Original** here, can be quickly redone with the Airbrush, or 5-point random brush in various colors.*

Note that with a limited palette of 16 or less, the performance of these two modes will depend on the color values available in the palette.
If you're smoothing red on a black background, but no dark red/brown color is available, PydPainter will do its best by using purple and dark grays. Under no circumstances will it alter the palette for you. 
## Gradient
**Gradient** Fills offer a host of creative uses. Their rendering will depend as much on the colors range chosen in the palette, the shapes drawn, as on the options selected here.
![](fill-ex.png)  
*Examples with a suite of 6 colors (3 bright yellow, cyan, blue and 3 white), a 7-color orange gradient and the default grayscale (12 colors).*

**Remember to select one of the Range colors as foreground color to select your gradient and get this type of preview.**

*to be continued and illustrated...*

## Dither
Dithering is the blending of pixels within a **Range** defined in Palette. Usually, it's a gradient, but it doesn't have to be. It can be regular, deactivated or, on the contrary, increasingly blended.
### Regular dithering
To use this quasi-geometric rasterization, pull the **Dither** slider all the way to the left.
![](Dithering-on.png)
### No dithering
If you don't want to use dithering, set the **Dither** slider to **0**.
![](Dithering-0.png)

### 1 to 20 dithering
The further the **Dither** slider is pulled to the right, the stronger the blend. Values range from 1 (very light) to 20 (a mishmash of colors).

![](Dithering-2.png)
Dither 2. The beginning of natural randomness.
![](Dithering-8.png)
Dither at 8. More of a mixture, it can be used as a base for coloring rocks or plants.
![](Dithering-20.png)
Max dithering (20). The gradient is barely recognizable. Can be used as a base before using other drawing modes such as Smooth or Blend.

