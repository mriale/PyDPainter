# Prefs Menu

This section allows you to adjust the default behavior of some functions to your liking.

Changes are effective immediately. They will not be remembered the next time **PyDPainter** is launched, unless you click on `Save Config`.

An active setting is preceded by a checkmark &check;.

- [Auto Transparency](#autotransp)
- [Hide Menus](#hide-menus)
- [Force 1:1 Pixels](#force-11-pixels)
- [True Symmmetry](#true-symmetry)
- [Coordinates](#coords)
- [Save Configuration](#save-config)

## AutoTransp
When this setting is on, PyDPainter ignores the current palette background color when grabbing a brush and uses instead the color of the 4 points at the corner of the brush capture rectangle.
If the four corners are the same color, that color becomes the transparent color, otherwise the current background color remains the transparent color.

Example: the palette background color is set to black. But with AutoTransp active, the brush takes this dark red as transparency.

![](Autotransp.jpg)

## Hide Menus
Menus at the top no longer appear automatically when the mouse is positioned over them. This emulates the way the Amiga menus did not appear until the right mouse button was pressed.

## Force 1:1 Pixels
This option forces PyDPainter to display only square pixels even when dealing with PAL or NTSC screen modes. Since modern displays have square pixels, this makes the all the pixels uniform when scaling to a modern display.

The pictures below show the non-square pixels and the resulting scaling artifacts of **NTSC** and **PAL** modes vs **1:1** pixels:<br>
![](NTSC-pixels.PNG)<br>
![](1-1-pixels.PNG)<br>
![](PAL-pixels.PNG)

## True Symmetry
Screen sizes are usually even numbers (like 320x200) which means there is no true center pixel to use with the symmetry tool. True Symmetry forces the center to half-pixels so the center of the symmetry is in the actual center of the screen.

This can be seen with a small 10x10 page size. On the left is regular symmetry and the on right is True Symmetry:<br>
![](true_symm.png)

## Coords
Displays mouse x and y coordinates in the menu bar. When drawing rectangles, circles, ellipses and brushes selection, the coordinates are replaced by the distance in pixels between the point of origin and your mouse position.  
![](rel-coords.PNG)

### Show
You can switch this option on and off in the Prefs menu or press `|` on the keyboard.

### Flip
In PyDPainter, the coordinates normally start at (0,0) in bottom left. When the Flip option is selected, it maps (0,0) to the top left.

### 1-based
The 1-based option starts the coordinates at (1,1) rather than (0,0).

*Note that part of your work page may be hidden under the menus at the top, and on the right under the toolbar. Press F10 to remove the menus, or use the arrow keys to move your work area.*

## Save Config
Save these choices in the config file for the next time you start **PyDPainter**.
If you wish to re-initialize the preferences, delete the `.pydpainter` file in your home directory.

###### Documentation written by Stephane Anquetil
