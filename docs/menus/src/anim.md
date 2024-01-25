# Anim Menu

Anim is new set of features in PyDPainter 2.x.

_Note : We're trying to implement all the features of Deluxe Paint 3. It's a foundation on which we're building, with our own enhancements such as GIF support and multi-palette mode. (check this ???)._

## General principle

Animation is a sequence of **frame**. Each frame is like an individual image on which you can draw independently. Animation is therefore the more or less rapid succession (see Control rate) of frames that produces an optical illusion of movement. In reality, nothing really moves. Remember the drawings on the bottom of a notebook that you scroll through rapidly with your finger. Think of early cartoons. Because of this principle, animation has a few limitations (which are those of the Deluxe Paint era):

- Screen size (Screen Fromat; Screen Size) cannot be changed during animation.
- The maximum number of colors displayed cannot be changed during animation. If you have a 16-color frame, the next frame cannot have 256 colors. If you need 256 colors at a given moment, the entire animation must be in 256 colors. Fortunately, you are no longer dependent on the memory limitations of the old days, unless you intend your work to be played back on a real Amiga.
- The palette can change during animation (Mode ), but it's simpler if it's the same everywhere (Global Mode).
- Most functions will draw on the current frame and not on the whole animation (except CLR and the forthcoming Move Requester). We work on frame-by-frame drawing.
- The maximum number of colors, even in AGA, is 256. PyDPainter is not, and will never be, a modern 16 million-color video or animation editor. You need to understand the "retro" spirit that draws creativity from the limitations of the time. The use of a limited number of colors allows for very particular effects and styles. It's also easier to draw this way. You can watch many examples on :
https://www.randelshofer.ch/animations/amiga.html

## Open…

This loads an animation in the following formats:
- Animated Gif (2 to 256 colors)
- ANIM5 (Amiga), from (n to x colors)
- ANIM8 (Amiga), from n to x colors (???)

_Note that since the Amiga doesn't need a .xxx file extension to recognize a file, you may come across ANIM files with no extension._

The Amiga's HAM mode (4096 simultaneous colors with constraints) is not and will not be supported, unless converted to 256 colors.


### Makedir

This button lets you create a directory without going back to Windows. When you're working with a series of images, it's really handy!

## Save… (Anim menu)

PyDPainter allows you to save your animations in the following formats:
- Animated Gif (2 to 256 colors)

_and coming soon_

*- ANIM5 (amiga), de (n to x colors)*

*- ANIM8 (Amiga), from n to x colors*

_There's no such thing as a " work project ", this saving only includes frames. So don't forget to save your draft page (j) as an image and the brushes you've used. in_ `Brush / Save as` Menu.

## Move…

The "move requester" is a powerful function that lets you move a brush throughout the animation, on the x, y and even z axes (perpective and rotation).
It will be implemented in the near future.

## Frames

### Import…

PydPainter can also load a sequence of numbered images. For example:
myanim_001.png to myanim_200.png
01.iff to 12.iff

You can, for example, load frame-by-frame renderings from other software, such as 3D or a series of scanned drawings.

The maximum number of frames depends on ??? (limit ???)

### Export…

Exports all frames of the animation as a numbered sequence of still images in the following formats:
- GIF
- IFF
- PNG ???

We advise you to do this in a folder (`Makedir` button) to avoid having hundreds of numbered files in a mess..

### Set #…
Sets the number of frames.  
_Ten frames may be enough for a test run. Remember that old cartoons use less than 15 frames per second._

### Copy to all
Copies the drawing of the current frame to all other frames.

### Add Frames
Adds one or several frames after the current frame. By doing so, it copies the contents of the frame currently displayed.

### Delete Frames
Delete this frame or several frame after the current frame.
_Please note that undo will not cancel this action._

### Delete All
Delete all frames, thus delete current animation and remove animation nav bar below.

## Control

Note that a navigation bar appears at the bottom of the screen whenever an animation is loaded or created. This "navbar" can be retracted using the `F10` key.

### Set Rate…
Defines the number of frames per second. This is the speed of your animation. At the time, it was not uncommon to see game intro or animation at 12 or 15 frames per second, for reasons of disk or memory space. Remember, your work will be better appreciated if people have time to look at it.

This speed can be global (for the whole animation) or local (the animation can speed up, for example, or remain "paused").

### Previous
Go back to the previous frame (if you're at frame 20, go back to 19). Keys `1` or `PageUp`

### Next

Go to next frame (if you're at frame 20, go to 21). Keys `2` or `PageDown`

### Go to…

Goes directly to the frame number you specify. If this number is greater than the total number of frames defined by [Set #...](#set), you've just reached the end. (??? check this)  
Key `3`

### Play
Plays the animation in a loop. When it reaches the last frame, it starts again without interruption. Key `4`. 
Hit `ESC` or `SPACE` to stop.

### Play once
Plays the animation once. Once it reaches the last frame, it stops.
Key `5`

### Ping-Pong
Play the animation in the normal direction (from the first to the last frame), then in the opposite direction, and start again.
Key `6`

## Anim Brush

_not yet implemented_  
Brushes become animated brushes in this powerful function that lets you draw an animation with an animation. For example, a spinning wheel or a walking monster crossing the screen.