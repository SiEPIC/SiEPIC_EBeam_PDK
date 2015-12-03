<?xml version="1.0" encoding="utf-8"?>
<klayout-macro>
 <description/>
 <version/>
 <category>pymacros</category>
 <prolog/>
 <epilog/>
 <doc/>
 <autorun>false</autorun>
 <autorun-early>false</autorun-early>
 <shortcut/>
 <show-in-menu>false</show-in-menu>
 <group-name/>
 <menu-path/>
 <interpreter>python</interpreter>
 <dsl-interpreter-name/>
 <text># Python script
# A* algorithm for waveguide path generation

"""
This file is part of the SiEPIC_EBeam_PDK
by Jaspreet Jhoja (c) 2015

This Python file takes an input for start and end point coordinates and generates an optimal path without crossing or overlapping the existing waveguides.

uses:
 - the SiEPIC EBeam GDS Library
 - the SiEPIC EBeam PCell Library

Version history:

Jaspreet Jhoja          2015/12/03

 - takes Manual coordinate input, if no coordinates are set,
    then the script automatically extract coordinates from the 
     start_pt and end_pt text.      
 - allows input for desired gap between waveguides
 - only works for waveguide width of 500nm 
 - usually takes 10-15 seconds, depending on the complexity of the obstacle
"""

# 
# Python script to create a layout for testing a double-bus ring resonator.
# uses:
#  - the SiEPIC EBeam GDS Library
#  - the SiEPIC EBeam PCell Library
# deletes everything first
#be patient, usually it takes around 14-15 seconds depending on the complexity of the obstacles







import pya
import sys, ast, copy, time, string
from shapely.geometry import LineString
global opened, closed, child_nodes, listtoget, barred_points, gap


opened = [] # stores all the generated but yet to visit nodes
closed = [] #stores all the visited nodes
child_nodes = [] # stores all the child nodes
barred_points = [] #points on 1d lines which are already taken
starting_pt=[0, 0]  #starting X and Y coordinates
goal_pt = [0,0]  #Goal C and Y coordinates
gap = 1000 #desired gap between waveguides. Default: 0.5um
wg_points = [] #list containing all the final backtracked path points



def find_points(topcell, LayerTextN):
  # find_automated_measurement_labels(topcell, LayerTextN)
  t = []
  dbu = topcell.layout().dbu
  iter = topcell.begin_shapes_rec(LayerTextN)
  i=0
  while not(iter.at_end()):
    if iter.shape().is_text():
      text = iter.shape().text
      if text.string.find("start_pt") &gt; -1:
        i+=1
        text2 = iter.shape().text.transformed(iter.itrans())
        t.append([text2.x, text2.y])
        #t += "label: %s, location: (%s, %s) &lt;br&gt;" %(text.string, text2.x*dbu, text2.y*dbu )
      if text.string.find("end_pt") &gt; -1:
        i+=1
        text2 = iter.shape().text.transformed(iter.itrans())
        t.append([text2.x, text2.y])
        #t += "label: %s, location: (%s, %s) &lt;br&gt;" %(text.string, text2.x*dbu, text2.y*dbu )
    iter.next()
 # t += "&lt;br&gt;*** Number of automated measurement labels: %s.&lt;br&gt;" % i
  return t

if(starting_pt == goal_pt):
  topcell = pya.Application.instance().main_window().current_view().active_cellview().cell
  LayerTextN = topcell.layout().layer(LayerText)
  t = find_points(topcell, LayerTextN)
  starting_pt = t[1]
  goal_pt = t[0]



# Configure variables to draw structures in the presently selected cell:
lv = pya.Application.instance().main_window().current_view()
if lv == None:
  raise Exception("No view selected")
# Find the currently selected layout.
layout = pya.Application.instance().main_window().current_view().active_cellview().layout() 
if layout == None:
  raise Exception("No layout")
cv = pya.Application.instance().main_window().current_view().active_cellview()
# find the currently selected cell:

if topcell == None:
  raise Exception("No cell")
# fetch the database parameters
dbu = layout.dbu

# Define layers based on PDK_functions:
LayerSiN = layout.layer(LayerSi)
LayerTextN = layout.layer(LayerText)
LayerPinRecN = layout.layer(LayerPinRec)
LayerDevRecN = layout.layer(LayerDevRec)
LayerFbrTgtN = layout.layer(LayerFbrTgt)
LayerErrorN = layout.layer(LayerError)
LayerINTERCONNECTN = layout.layer(LayerINTERCONNECT)
LayerSi = pya.LayerInfo(1, 0)
#LayerSiN = cell.layout().layer(LayerSi)
fpLayer = pya.LayerInfo(99, 0)
#fpLayerN = cell.layout().layer(fpLayer)
TextLayer = pya.LayerInfo(10, 0)
#TextLayerN = cell.layout().layer(TextLayer)

# Clear the previous errors:
clear_ErrorLayer(topcell, LayerErrorN)


############################################################################
####  PHASE -1 : Extract points which are already taken ####################
############################################################################

# initialize the arrays to keep track of layout objects
reset_Optical_classes()
optical_components = []
optical_waveguides = []
optical_pins = []
optical_nets = []

# Create a Results Database
rdb_i = lv.create_rdb("SiEPIC_Verification")
rdb = lv.rdb(rdb_i)
rdb.top_cell_name = topcell.name
rdb_cell = rdb.create_cell(topcell.name)

# Search the layout for the components and waveguides:
# Search the arrays to identify all the nets:
optical_waveguides, optical_components, clock_find_all_components, clock_find_all_waveguides, clock_identify_all_nets \
  = netlist_extraction(topcell)

b_points = []  #list containing extracted waveguide points and their widths
for i in optical_waveguides:
  converted_points = i.points
  b_points.append([i.wg_width*1e3,converted_points])

#following loop generates coordinates for the area which needs to be avoided 
for i in b_points:
  diff = i[0]*2 #wg_width
  c_data = i[1] #copy data
  c1 = copy.deepcopy(c_data) 
  c2 = copy.deepcopy(c_data)
  c3 = copy.deepcopy(c_data)
  c4 = copy.deepcopy(c_data)
  
  for j in c1:
    j[0] = j[0] + (diff)
  
  for k in c2:
    k[0] = k[0] - (diff)
  
  for l in c3:
    l[1] = l[1] + (diff)
    
  for m in c4:
    m[1] = m[1] - (diff)
  
  barred_points.append(c1)
  barred_points.append(c2)
  barred_points.append(c3)
  barred_points.append(c4)
  
  
#barred_points contains the data about the restricted areas

  
###########################################################################  
############ PHASE -2 : DEFINING NODE AND A* Algorithm ####################
###########################################################################


#defining a node
class node:
  data = [] #grid data in x,y
  parent = None#its parent
  mvalue = 0   #heuristic value
  gvalue = 0   #path cost
  fvalue = 0   #total function cost
  goal = [-2950,-500] 
  restricted = 0

  def __init__(self, grid, head):
    self. data = grid #load grid starting point data
    self. parent = head #defining its parent
    self.manhattan()
    if(head == None):
      self.gvalue = 0
    else:
      self.gvalue = head.gvalue + 1
    
    self.fvalue = self.gvalue + self.mvalue
    
    
  def manhattan(self):  #This is a heuristic estimate function
      self.mvalue = 0
      self.mvalue = abs(self.data[0]-self.goal[0]) + abs(self.data[1]-self.goal[1])
        
  
  def generatechild(self):
     #This function generates all possible children of a node
      clist = []
      
      data1 = copy.deepcopy(self.data)
      data1[0] = data1[0]+50
      ch1 = node(data1,self)
      
      data2 = copy.deepcopy(self.data)
      data2[0] = data2[0]-50
      ch2 = node(data2,self)
      
      data3 = copy.deepcopy(self.data)
      data3[1] = data3[1]+50
      ch3 = node(data3,self)
      
      data4 = copy.deepcopy(self.data)
      data4[1] = data4[1]-50
      ch4 = node(data4,self)
      
      #Check if any of the children lies in the restricted areas, if it does then mark it restricted
      if(len(closed)&gt;=1):
      
        for i in barred_points:
          p1 = LineString(i)
          p2 = LineString([closed[-1].data,ch1.data])
          if(p1.intersects(p2)==True):
            ch1.restricted = 1
   
          p2 = LineString([closed[-1].data,ch2.data])
          if(p1.intersects(p2)==True):
            ch2.restricted = 1        
          
  
          p2 = LineString([closed[-1].data,ch3.data])
          if(p1.intersects(p2)==True):
            ch3.restricted = 1          
            
          p2 = LineString([closed[-1].data,ch4.data])
          if(p1.intersects(p2)==True):
            ch4.restricted = 1          
            
      #If a child is not in restricted area then add it to the valid children list, clist
      if(ch1.restricted == 0):
        clist.append(ch1)
      if(ch2.restricted == 0):
        clist.append(ch2)
      if(ch3.restricted == 0):
        clist.append(ch3)
      if(ch4.restricted == 0):
        clist.append(ch4)
      
      return clist
    
    
    
def Astar():
  #initiates lists
  global opened, closed, child_nodes, current_node, listtoget
 
 #create starting node 
  start_node = node(starting_pt,None)
  start_node.goal = goal_pt
  #Add the node to the open list
  opened.append(start_node)
  
 # print start_node.data
  
  while(len(opened)&gt;0): #while there are no instances to test
    opened = sorted(opened, key=lambda x: x.fvalue) #sort the open list in an order of ascending fvalues. 
    current_node = opened[0] #select the one with less cost or recommended by the heuristic
    
    if(current_node.data == current_node.goal): #If node meets the goal then print out
        closed.append(current_node)
        return ("Success.")
        
    opened.pop(0) #remove the component from the opened list
    child_nodes = [] #create an empty list to contain its child nodes
    child_nodes = current_node.generatechild() # generate its children

    try:

      for each in child_nodes:
          if(any(y.data == each.data for y in closed) == True): #if successor is in the closed list, skip it
            continue

          if(any(x.data == each.data for x in opened) == True): #if successor is in the open list, check if the existing node has smaller gvalue than successor 
                             for i in opened:                   # If it does, then update the existing node
                               if((i.gvalue&gt;each.gvalue) and (i.data == each.data)):
                                 i.gvalue = each.gvalue
                                 i.parent = each.parent


          else:   #Otherwise add it to the open list
            opened.append(each)
    except Exception as e:
      None

    closed.append(current_node)  #Add current node to the closed list


def backtrack(a):#This function backtracks and stores points for optimal path in a list
  global duplicate
  duplicate.append(a.data)
  a = a.parent
  if(a.data == starting_pt):
    return ""
  backtrack(a) 
  
  
def draw(): #This function is responsible for drawing on the star
        global closed, ref_pt, duplicate
        duplicate = []
        ref_pt = closed[-1]

        backtrack(ref_pt)       

        duplicate.reverse()

        for i in duplicate:
          pt = i
          pt[0]= float(pt[0]*1e-3)
          pt[1] =float(pt[1]*1e-3)
          wg_points.append(pt)
        cell = pya.Application.instance().main_window().current_view().active_cellview().cell
      #  cell = cell.layout().create_cell("MZI_TE_Variations")
        #cell = pya.Application.instance().main_window().current_view().active_cellview().cell
        L1 = layout_waveguide_abs(cell, LayerSi, wg_points , 0.5, 1)
  
Astar()
draw()</text>
</klayout-macro>
