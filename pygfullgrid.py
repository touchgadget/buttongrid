#!/usr/bin/env python3
"""
Grid of buttons sending MIDI. A minimal touchscreen version of a MIDI Fighter
button controller.
Tested on Raspian python3 pygame 2.0.0 dev6
pip3 install pygame==2.0.0.0.dev6
"""

import sys
import json
import pygame
import pygame.midi
from pygame.locals import *

GridDef = json.load(open("gridmidi.json"))
if not GridDef:
    print("Warning, gridmidi.json file not found")
    sys.exit()
GridCells = GridDef["gridcells"]
if not GridCells:
    print("Warning, gridcells not in JSON file")

if not pygame.font:
    print("Warning, fonts disabled")
if not pygame.mixer:
    print("Warning, sound disabled")
if not pygame.midi:
    print("Warning, midi disabled")

def _print_device_info():
    for i in range(pygame.midi.get_count()):
        r = pygame.midi.get_device_info(i)
        (interf, name, input, output, opened) = r

        in_out = ""
        if input:
            in_out = "(input)"
        if output:
            in_out = "(output)"

        print ("%2i: interface :%s:, name :%s:, opened :%s:  %s" %
               (i, interf, name, opened, in_out))

pygame.init()
pygame.midi.init()

_print_device_info()
MIDIPort = GridDef.get("MIDIPort")
if not MIDIPort:
    MIDIPort = pygame.midi.get_default_output_id()
print ("using output_id :%s:" % MIDIPort)
if MIDIPort == -1:
    midi_out = False
else:
    midi_out = pygame.midi.Output(MIDIPort, 0)

#Create a display surface object
DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
(screen_width, screen_height) = DISPLAYSURF.get_size()
pygame.mouse.set_visible(False)

buttonOnColor = GridDef.get("buttonOnColor")
if buttonOnColor == None:
    buttonOnColor = (240, 240, 240)
height = GridDef.get("gridheight")      # grid height in cells
if height == None:
    height = 8
width = GridDef.get("gridwidth")        # grid width in cell
if width == None:
    width = 12
gridlines = GridDef.get("gridlines")    # grid lines
if gridlines == None:
    gridlines = 1
cell_height = screen_height / height
cell_width = screen_width / width
background_color = (64, 64, 64)
fingers = {}

if pygame.font:
    font = pygame.font.Font(None, 72)

def displayToCellIndex(x, y):
    """ Convert screen/display co-ordinates to cell array offset """
    return int(y/cell_height)*width + int(x/cell_width)

def touchToCellIndex(x, y):
    """ Convert touch co-ordinates to cell array offset """
    return int(y*height)*width + int(x*width)

def buttonDraw(color, gridcell):
    button_center = gridcell["button_center"]
    button_radius = gridcell["button_radius"]
    pygame.draw.circle(DISPLAYSURF, color, button_center, button_radius)
    text = gridcell["text"]
    textpos = gridcell["textpos"]
    DISPLAYSURF.blit(text, textpos)

def buttonOn(gridcell):
    MIDINote = gridcell["MIDINote"]
    if midi_out:
        midi_out.note_on(MIDINote, 127)
    buttonDraw(buttonOnColor, gridcell)
    gridcell["noteOn"] = True
    pygame.display.update(gridcell["rect"])

def buttonOff(gridcell):
    MIDINote = gridcell["MIDINote"]
    if midi_out:
        midi_out.note_off(MIDINote, 127)
    buttonDraw(gridcell["buttonColor"], gridcell)
    gridcell["noteOn"] = False
    pygame.display.update(gridcell["rect"])

# Draw grid of size width x height. Each element of the grid is a cell
# of cell_width x cell_height. Each cell has a buttons and label.
# For example, given a screen size of 1920 x 1080 and a grid 12 cols and 8
# rows, cell_width = 1920 / 12 and cell_height = 1080 / 8
for y in range(height):
    for x in range(width):
        gridcell = GridCells[y*width+x]
        gridcell["noteOn"] = False
        if gridcell.get('sticky') == None:
            gridcell["sticky"] = False
        rect = pygame.Rect(x*cell_width, y*cell_height, cell_width, cell_height)
        gridcell["rect"] = rect
        pygame.draw.rect(DISPLAYSURF, background_color, rect, 0)
        cell_center = (int(x*cell_width+cell_width/2),
                int(y*cell_height+cell_height/2))
        button_color = gridcell["buttonColor"]
        gridcell["button_center"] = cell_center
        gridcell["button_radius"] = button_radius = int(cell_height/2)
        pygame.draw.circle(DISPLAYSURF, button_color, cell_center,
                button_radius)
        gridcell["text"] = text = font.render(gridcell["label"], 1, (10, 10, 10))
        gridcell["textpos"] = textpos = text.get_rect(center=cell_center)
        DISPLAYSURF.blit(text, textpos)
    if gridlines:
        # Draw horizontal grid lines
        pygame.draw.line(DISPLAYSURF, (0, 0, 0),
                (0, y*cell_height), (screen_width-1, y*cell_height))
if gridlines:
    # Draw vertical grid lines
    for x in range(width):
        pygame.draw.line(DISPLAYSURF, (0, 0, 0),
                (x*cell_width, 0), (x*cell_width, screen_height-1))
pygame.display.update()

mainLoop = True

while mainLoop:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            mainLoop = False
        elif event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE:
                mainLoop = False
        elif event.type == pygame.MOUSEBUTTONUP:
            gridcell = GridCells[displayToCellIndex(event.pos[0], event.pos[1])]
            if not gridcell["sticky"]:
                if gridcell["noteOn"]:
                    buttonOff(gridcell)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            gridcell = GridCells[displayToCellIndex(event.pos[0], event.pos[1])]
            if gridcell["sticky"]:
                if gridcell["noteOn"]:
                    buttonOff(gridcell)
                else:
                    buttonOn(gridcell)
            else:
                if not gridcell["noteOn"]:
                    buttonOn(gridcell)
        elif event.type == pygame.MOUSEMOTION and event.buttons[0] == 1:
            gridcell_new = GridCells[displayToCellIndex(event.pos[0], event.pos[1])]
            if gridcell_new != gridcell:
                if not gridcell["sticky"]:
                    if gridcell["noteOn"]:
                        buttonOff(gridcell)
                    if not gridcell_new["noteOn"]:
                        buttonOn(gridcell_new)
                gridcell = gridcell_new
        elif event.type == pygame.FINGERDOWN:
            cellIndex = touchToCellIndex(event.x, event.y)
            fingers[event.finger_id] = cellIndex
            gridcell = GridCells[cellIndex]
            if gridcell["sticky"]:
                if gridcell["noteOn"]:
                    buttonOff(gridcell)
                else:
                    buttonOn(gridcell)
            else:
                if not gridcell["noteOn"]:
                    buttonOn(gridcell)
        elif event.type == pygame.FINGERUP:
            cellIndex = touchToCellIndex(event.x, event.y)
            fingers[event.finger_id] = cellIndex
            gridcell = GridCells[cellIndex]
            if not gridcell["sticky"]:
                if gridcell["noteOn"]:
                    buttonOff(gridcell)
        elif event.type == pygame.FINGERMOTION:
            cellIndex = touchToCellIndex(event.x, event.y)
            gridcell_new = GridCells[cellIndex]
            gridcell = GridCells[fingers[event.finger_id]]
            if gridcell_new != gridcell:
                if not gridcell["sticky"]:
                    if gridcell["noteOn"]:
                        buttonOff(gridcell)
                    if not gridcell_new["noteOn"]:
                        buttonOn(gridcell_new)
                fingers[event.finger_id] = cellIndex

if midi_out:
    del midi_out
pygame.midi.quit()
pygame.quit()
