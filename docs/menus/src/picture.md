# Picture Menu

_Work in progress..._

## New...

Shows the [Screen Format requestor...](screenformat.md) to allow you to choose a new canvas to paint on.

*Tip: remember that pixel art spirit is low screen resolution with all pixels visible on the screen. Similarly, the number of colors used is limited, as is the number of tints available.* 


## Open...
Loads bitmap images in the following formats:
*  .iff or .ilbm (Amiga legacy), from 2 to 16 million colors (conversion to 256 colors max)
* .lbm PC IFF PBM (???)
* .bmp Windows BitMaP image (up to 256 colors)
* .gif GIF (still image. Animated GIFs are supported, but in the animation menu)
* .jpg .jpeg JPEG, a lossy photo compression format (conversion to 256 colors)
* .png (conversion to 256 colors if necessary)
* .tga Targa images

> Please note! The size of modern images may exceed **PydPainter** inbuilt screen sizes, in which case they will be larger and continue beyond the screen displayed, below the interface. You can scroll them using cursors keys. [see Page Size](#page-size).


The file query is inspired by **DeluxePaint** legacy. You can move up one level in the tree structure by clicking on `.. (parent dir)`
Above all, you can change the drive by directly typing its letter in the path:  
`D:\`  
`C:\Users\Utilisateur\Pictures\`

If you're not used to DOS paths, Windows Explorer can show you the DOS path. Take any file explorer window. Just click on the little (yellow?) icon just before the normal path. i.e.:  
icon `> This PC > DATA (D:) > Test > PydPainter > iff_pics` which then changes to  
`D:\TestT\PyDPainter\iff_pics`.

> You can download sample images from the [Amiga picture archive here](https://amiga.lychesis.net/index.html).
> In some cases, click on the little disk icon with the IFF arrow to download an image that you can view "in its original state" here and see how the colors have been used, cycled, etc.

### Conversions
**PydPainter** is not designed as a high-performance conversion tool. If you need to convert an image to PD's low-resolution, indexed color formats, you can use the following tools:  
- [Online conversion tool](http://tool.anides.de/)
- A display/converter such as [XNView](https://www.xnview.com/en/xnview/)
- You can alse use any old ***Adobe PhotoShop**. It still saves images in the Amiga's iff format.
## Save
Saves the image in the same format as you loaded it, without warning.
## Save as...
Saves the image by requesting the desired format. You can choose from the same formats as with open. Use the small drop-down menu to the right of the file name.
## Revert
Reloads the image as you last loaded or saved it. Be careful, it will remove everything you've done since then. Handy if you want to try things out from within an image.
## Print...
_not supported_
## Flip
Immediately performs an inversion on the entire image.
### Horiz
horizontally (right-left reversal)
### Vert
vertically (up-down flipping)
## Change Color
With a palette often limited to only 32 or 16 colors, you'll need precise color management. That's what these tools are for.
### [Palette…](palette.md)
### Use Brush Palette
Abruptly replaces the palette with that of the last `Brush` you load.
*If you're not into psychedelic effects, you'll probably want to use the [Remap](#remap) function after this.*
### Restore Palette
Go back to the previous palette (I'm not sure ???)
### Default Palette
Replaces current palette with default palette (which is **PydPainter**'s palette, inspired by **DeluxePaint**'s palette)

*If you're not into psychedelic effects, you'll probably want to use the [Remap](#remap) function after this.*

### Cycle
### BG -> FG
### BG <-> FG
### Remap
## Spare
### Swap
### Copy To Spare
### Merge in front
### Merge in back
## Page Size...
## Show Page
## [Screen Format...](screenformat.md)
## About...
## Quit

