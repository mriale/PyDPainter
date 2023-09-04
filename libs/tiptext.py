#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

tiptext = {}

lbf = "- left button for foreground color"
rbb = "- right button for background color"

outline = "Upper left of tool draws an outline"
filled = "Lower right of tool draws a filled area"
dragshape = "Drag out shape on canvas."

tiptext["dot"] = [
"Dot Tool [s]",
"Drag out dotted strokes on canvas.",
lbf, rbb]

tiptext["draw"] = [
"Draw / Area Tool",
"Upper left of tool is Draw [d]",
"Lower right of tool is filled Area [D]",
"Drag out continuous strokes on canvas.",
lbf, rbb]

tiptext["line"] = [
"Line Tool [v]",
"Drag out straight line on canvas.",
lbf, rbb,
"Right-click tool to adjust Spacing. [V]"]

tiptext["curve"] = [
"Curve Tool [q]",
"1. Drag out straight line on canvas",
"2. Move mouse to adjust curve",
"3. Click again to finalize curve",
lbf, rbb,
"Right-click tool to adjust Spacing."]

tiptext["fill"] = [
"Fill Tool [f]",
"Click to fill an enclosed area.",
lbf, rbb,
"Right-click tool to adjust Fill. [F]"]

tiptext["airbrush"] = [
"Airbrush Tool",
"Hold button to spray dots randomly around cursor.",
lbf, rbb,
"Hold [CTRL] key to slow down spray rate.",
"Right-click tool to adjust spray size."]

tiptext["rect"] = [
"Rectangle Tool",
outline + " [r]",
filled + " [R]",
dragshape,
lbf, rbb]

tiptext["circle"] = [
"Circle Tool",
outline + " [c]",
filled + " [C]",
dragshape,
lbf, rbb]

tiptext["ellipse"] = [
"Ellipse Tool",
outline + " [e]",
filled + " [E]",
dragshape,
"Drag again to rotate.",
lbf, rbb]

tiptext["poly"] = [
"Polygon Tool",
outline + " [w]",
filled + " [W]",
"Drag out straight lines on canvas.",
"Finish at starting point to complete polygon.",
lbf, rbb]

tiptext["brush"] = [
"Brush Tool [b] (rectangle or polygon)",
"Click brush tool again to toggle rectangle or polygon shape.",
"Draw shape on canvas to pick up brush.",
"- left button to copy canvas",
"- right button to cut out canvas with background color"]

tiptext["text"] = [
"Text Tool [t]",
"Click on canvas to place text cursor.",
"Type text on keyboard to draw text",
"Right-click tool to change font"]

tiptext["grid"] = [
"Grid Toggle [g]",
"Modifies tools to snap brush to grid.",
"Right-click tool to adjust grid."]

tiptext["symm"] = [
"Symmetry Toggle [/]",
"Modifies tools to duplicate brush along lines of symmetry.",
"Right-click tool to adjust symmetry type and degree."]

tiptext["magnify"] = [
"Magnifier Toggle [m]",
"Shows canvas magnified for detail work.",
"Click on canvas to place magnifier bounding box.",
"- cursor keys move magnified area",
"- press [n] to center magnified area over a point"]

tiptext["zoom"] = [
"Zoom magnifier in [>] or out [<]",
"Makes pixels on magnified canvas larger or smaller.",
"Left-click tool to zoom in [>]",
"Right-click tool to zoom out [<]",
"Scroll wheel on canvas zooms in and out."]

tiptext["undo"] = [
"Undo [u] / Redo [U] Tool",
"Left-click tool to undo [u] last change to canvas.",
"Right-click tool to redo [U] last change to canvas.",
"There are multiple levels of undo/redo"]

tiptext["clear"] = [
"Clear Tool [K]",
"Clear canvas to background color."]

tiptext["swatch"] = [
"Color Swatch / Palette [p] / Pick [,]",
"Displays current foreground color",
"surrounded by background color.",
"Left-click to pick color from canvas [,]",
lbf, rbb,
"Right-click tool to adjust color palette. [p]"]

tiptext["palette"] = [
"Color Palette",
"Shows current color palette with foreground color outlined.",
"Left-click tool to select foreground color",
"Right-click tool to select background color"]

tiptext["circle1"]   = ["Single pixel brush"]
tiptext["circle2"]   = ["Small circle brush"]
tiptext["circle3"]   = ["Medium circle brush"]
tiptext["circle4"]   = ["Large circle brush"]
tiptext["square1"]   = ["2x2 pixel square"]
tiptext["square2"]   = ["3x3 pixel square"]
tiptext["square3"]   = ["4x4 pixel square"]
tiptext["square4"]   = ["5x5 pixel square"]
tiptext["spray1"]    = ["Small spray brush"]
tiptext["spray2"]    = ["Large spray brush"]

tiptext["expand"]    = ["Expand or contract mini toolbar"]
tiptext["help"]      = ["Toogle help bubbles on or off"]
tiptext["scale"]     = ["Scale window to be larger or smaller"]
tiptext["fullscreen"]= ["Toggle full-screen mode [F11]"]
tiptext["scanlines"] = ["Toggle retro CRT scanline simulation"]
tiptext["aspect"]    = ["Select whether pixels are square or rectangular"]
