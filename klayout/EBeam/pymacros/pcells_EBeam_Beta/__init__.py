import os, sys
import SiEPIC
from SiEPIC.utils import get_technology, get_technology_by_name
from pya import *
import math

path = os.path.dirname(os.path.abspath(__file__))

def linspace_without_numpy(low, high, length):
    step = ((high-low) * 1.0 / length)
    return [low+i*step for i in range(length)]

def pin(w,pin_text, trans, LayerPinRecN, dbu, cell):
  """
  w: Waveguide Width, e.g., 500 (in dbu)
  pin_text: Pin Text, e.g., "pin1"
  trans: e.g., trans =  Trans(0, False, 0, 0)  - first number is 0, 1, 2, or 3.
  pinrec: PinRec Layer, e.g., layout.layer(TECHNOLOGY['PinRec']))
  devrec: DevRec Layer, e.g., layout.layer(TECHNOLOGY['DevRec']))
  """
  
  # Create the pin, as short paths:
  from SiEPIC._globals import PIN_LENGTH

  pin = trans*Path([Point(-PIN_LENGTH/2, 0), Point(PIN_LENGTH/2, 0)], w)
  cell.shapes(LayerPinRecN).insert(pin)
  text = Text (pin_text, trans)
  shape = cell.shapes(LayerPinRecN).insert(text)
  shape.text_size = w*0.8

  # print("Done drawing the layout for - pin" )
