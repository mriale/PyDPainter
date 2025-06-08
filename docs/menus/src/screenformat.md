# Screen format

_Work in progress..._

- [Screen format](#screen-format)
  - [What is a screen format ?](#what-is-a-screen-format-)
  - [Tools bar and menu](#tools-bar-and-menu)
  - [Quick tutorial : displaying Kingtut.](#quick-tutorial--displaying-kingtut)
  - [Format:](#format)
  - [Systems](#systems)
    - [NTSC and PAL](#ntsc-and-pal)
    - [VGA](#vga)
    - [Lo-Res](#lo-res)
    - [Med-Res](#med-res)
    - [Interlace](#interlace)
    - [Hi-Res](#hi-res)
  - [Number of colors](#number-of-colors)
  - [Out of](#out-of)
    - [4096](#4096)
    - [16M](#16m)
  - [Resize Page](#resize-page)
- [Bottom buttons](#bottom-buttons)
    - [Cancel](#cancel)
    - [OK](#ok)
    - [Make Default](#make-default)
          - [Documentation written by Stephane Anquetil](#documentation-written-by-stephane-anquetil)

## What is a screen format ?

Imagine you are drawing a picture using tiny colored squares, called pixels. The more squares you use, the more detailed your picture can be. This is what we call "screen resolution"—it’s the number of tiny squares that make up the images on a computer screen. But increasing the number of pixels has a cost: you need the graphic memory to store them, the storage to save them, the screen to display them, and the power to animate them in games or even animations. In the 80s and 90s, none of this was obvious.
A long time ago, when people played games on computers like the Amiga, Atari ST, or early PCs, the screens didn’t have as many pixels as today. For example:
- On the Amiga or Atari ST, many games used a screen resolution of 320 by 256 pixels. That means the screen was made up of 320 little squares across and 256 down.
- It used 320 by 200 pixels for most demos and games, though it could go higher for things like writing or music programs, but with fewer colors.
- Early PCs, like those using VGA graphics, had a mode with 320 by 200 pixels and 256 colors, or 640 by 480 pixels with 16 colors.

![](Kingtut-ntsc.jpg)
*The iconic Tutankhamun mask used as cover for many Deluxe Paint versions. 320x200 NTSC picture in 32 colors by Avril Harrison.*


It's these screen modes that form the basis of **PyDPainter**, even if it may seem obsolete, because this programme is first and foremost a recreation of **DeluxePaint III**, as it was conceived at the time.

Because there weren’t many pixels and colors, artists made beautiful pictures and characters using what is now known as "pixel art." Pixel art is when you create pictures by carefully choosing the color of each little square. It’s like making a mosaic with beads or LEGO blocks, where every piece counts!

Even though these pictures were not as realistic as modern photos and videogamess, they had their own special charm. Artists used clever tricks to make the images look lively and colorful, even with just a few pixels and colors. For example, games by Bitmap Brothers or Psygnosis on the Amiga are still remembered for their amazing pixel art

That’s why pixel art and low-resolution graphics are not just old—they’re beautiful in their own way, and they remind us of how creative people can be, even with simple tools! **PydPainter** is the ideal tool for getting started with pixel art or studying how it was done back in the day.

## Tools bar and menu

Another important legacy is that, at the time, screens and resolution were not large enough to distinguish the working document from the interface. Today, you work with tool palettes and menus that you place wherever you want, independently of your open documents. In **PydPainter**, the toolbar on the right and the menus follow your screen resolution. And, as in the old days, you can draw ‘underneath’. 

![Picture with menu](640x256_menus.jpg)
*Original Amiga with a real CTR screen displaying Deluxe Paint with its tool and menu bars.*

![Picture with menu](640x256_1.jpg)

*Full picture (640x256 px aka Med-Res)*
## Quick tutorial : displaying Kingtut.

1. Go at [Amiga Lychensis Archive](https://amiga.lychesis.net/applications/DeluxePaint.html). Select Applications, Deluxe Paint. Scroll down to the middle of the page, locate the King Tutankhamun picture.
2. Click on the IFF dowload icon on the upper right and save the AH_KingTut.iff Amiga file on your computer.
3. Locate it and load it into **PyDPainter**, using Drag'n'Drop or the **"Picture / Open..."** menu.
4. If you look closely at the image of KingTut again, the menu bar at the top hides the upper part of the image. Scroll with the `Up` and `Down` Keys of your keyboard.
5. Use the `F10` key to try it. It hide and switch the toolbars.
6. Hit the `F12` key to browse through the CRT and antialising screen emulations. Identify the display you prefer.
7. Check the **Picture / Screen Format...**. It disply the current Screen Format. Lo-Res 320x200 (NTSC), 32 colors out of 4096 (Legacy Amiga).
![](Kingtut-ntsc-scr.jpg)
9. Hit Cancel.

## Format:
The list is updated according to the **system** display selected by the 3 buttons at the bottom. A choice from this list may restrict the **Number of Colors** on the left.

## Systems
 With **PyDPainter**, you get a kind of Deluxe Paint AMIGA III (OCS/ECS), DPaint AGA modes, and PC for the same price *– for free*.
### NTSC and PAL
**NTSC** was the ‘Nord America’ video signal for TV broadcasting. In low-res, it's limited to 480 lines in Overscan, while European/Asian **PAL** has 576 more. Consequently, to cover a cathode-ray screen or TV Screen, the appearance of the pixels is not the same. Refresh rates were different too. NTSC is just below 30 IPS, PAL at 50 Hz, mainly using 25 IPS. This is pointless now. Others settings are the same into PyDPainter. For more info about [Amiga Screen mode](https://amiga.lychesis.net/articles/ScreenModes.html).

The Amiga had a 4096-colour mode at the same time on screen, known as **HAM** (Hold And Modify). Although very impressive for 3D renderings, photo scans and slide-shows, it has constraints which produced the colour smears, typical of this mode. This very specific graphic mode will not be supported by **PydPainter**, but loaded HAM images will be converted to 256 colours.

Name | Resolution in pixels | Colors
--- | --- | ---
Lo-Res | 320x256 | 2 to 32 colors or EHB
Med-Res | 640x256 | 2 to 16 colors
Interlace | 320x512 | 2 to 32 colors or EHB
Hi-Res | 640x512 | 2 to 16 colors

The main Amiga formats are supported, from 2 up to 256 colors. If you want to relive the experience and constraints of an Amiga 500, 600, 2000 or 3000, stick with **4096** colours palette. If you prefer to use 256 colours or see what an A1200 or A4000 could do, press **16M** (16 777 216 colors as modern computers).

### VGA
**VGA** was the screen format used on PCs at the time. All are 2 to 256 colors out of 16 millions colors for simplification, even if it's historically wrong. If you want to recreate Sierra's King'Quest CGA screens, use MCGA and lower the colors to 16.
Name | Resolution in pixels | Colors
--- | --- | ---
MCGA | 320x200 | 2 to 256 colors
VGA | 640x480 | 2 to 256 colors
SVGA | 800x600 | 2 to 256 colors
XGA | 10234x768 | 2 to 256 colors

### Lo-Res 
This was the resolution of the majority of Amiga (or Atari, SNES) games and demos. The pixel is slightly elongated in PAL.
### Med-Res
This was the Workbench's AmigaOS default screen resolution. The pixel has that distinctive narrow 1:2 aspect ratio that allows more letters to be displayed on each line. If you've experienced it on a real Amiga, it was often limited to 4 colours for reasons of graphic memory size (CHIP RAM). All Amiga program icons used this mode.
### Interlace
An ideal format for scans and impressive loading screens, but with the major drawback of flickering horribly on a TV or CRT monitor (at the time). Pixel is 2:1 ratio. Remember James Dean's illustration on Shadow of the Beast or the Unreal title screen? That was this screen format!
### Hi-Res
The high-resolution screen. Ideal for word processing, DTP, vector or 3D software, but required a VGA screen with a desinterlace card to avoid blowing your eyes out. Pixel is 1:1 again, but smaller.

*It's double the low-res, so if you change **Screen Format** to Hi-Res after you've finished your picture and click **Yes** to Resize, it doubles the image size easily.*

## Number of colors
You can choose from 2 up to 256 colors. Even if it can be tempting to choose the maximum of 256 colours, pixel art is the art of constraint, you will learn more and the software will be easier to handle and understand with fewer colours. 32 is a good beginning.

**EHB** is **Extra Half Brite**, a special Amiga Mode, which the last 32 colors are half the value of the first 32 colors. Used in conjunction with **Halfbrite Mode** (_not yet supported_), this is a prodigious drawing mode for managing shadows or lighten/darken effects. Unfortunatly, only a few games use it as 1990s Super Cars I and II, and 1992s Black Crypt. Agony and Magnetic Field's Lotus Turbo Esprit Challenge 2 use this mode for loading screens. More info at [Amiga Graphics Archive](https://amiga.lychesis.net/articles/ExtraHalfBright.html target:_blank)

## Out of
The Amiga 500/600/2000/3000 (OCS/ECS) had a palette of **4096** colours (which was already top-of-the-range at the time of their launch). With the AGA chipset, Amiga 1200/3000/CD32 introduced **16 million** colours to catch up with technological developments. This is still the standard today, because in fact the human eye rarely distinguishes more nuances.
### 4096
In the [Palette](palette.md), each Red, Green, Blue slider has a limited 16 value scale.
### 16M
Modern palette. In the [Palette](palette.md), each Red, Green, Blue slider has a 256 value scale.
![](screen-format.jpg)

## Resize Page
Click **Yes** if you want to resize the current image to the new screen size. For example, if you start with a Lo-Res image and go to Hi-Res, this will double the height and length of the image. One pixel will be up to 4. The sharpness of your drawing will not be automatically increased, but the image will be 4 times larger (ideal for publishing on a social network).

Click on **No**, if you want to keep the image as it is. This is particularly useful if you want to scale the image from large to small so that it doesn't have to be resized. The image will then be larger than the working screen. See [Page Size](picture.md#page-size), so use the arrow keys.

# Bottom buttons
### Cancel
Cancel any change. Nothing happens.
### OK
Use the new Screen Format. Current picture may be altered, depending of your choice (less colors, smaller, bigger, etc)
### Make Default
Save to use this Screen Format each time **PyDPainter** is launched or the **New... Picture** menu is used.

###### Documentation written by Stephane Anquetil
