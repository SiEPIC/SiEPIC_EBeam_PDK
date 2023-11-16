
'''
Create a layout of a paperclip spiral
by Lukas Chrostowski, 2023

- this can be executed directly, or loaded by the technology library
- you can resize the PCell by using the Partial select tool "L", and moving 
   the GUIDING SHAPE Box
- Waveguide types are loaded from the XML file
- Pitch of the waveguides is determined by the DevRec layer
   
'''


import pya
from pya import *

class spiral_paperclip(pya.PCellDeclarationHelper):

    def __init__(self):
        # Important: initialize the super class
        self.cellName=self.__class__.__name__
        super(eval(self.cellName), self).__init__()
        
        from SiEPIC.utils import get_technology_by_name, load_Waveguides_by_Tech
        self.technology_name = 'EBeam' 
        self.TECHNOLOGY = get_technology_by_name(self.technology_name)
                        
        # Load all strip waveguides
        self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)   
            
        # declare the parameters
        p = self.param("waveguide_type", self.TypeList, "Waveguide Type", default = self.waveguide_types[0]['name'])
        for wa in self.waveguide_types:
            p.add_choice(wa['name'],wa['name'])
        
        self.param("loops", self.TypeInt, "Number of loops", default = 2)
        self.minlength = 2*float(self.waveguide_types[0]['radius'])
        self.param("length1", self.TypeDouble, "Inner length (min 2 x bend radius)", default = self.minlength)
        self.param("box", self.TypeShape, "Box", default = pya.DBox(-self.minlength, -self.minlength/2, self.minlength, self.minlength/2))
        self.param("length", self.TypeDouble, "length: for PCell", default = self.minlength, hidden = True)
        
    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "%s_%s_%s_%s" % (self.cellName, self.loops, self.length, self.waveguide_type.replace(' ','_'))

    def coerce_parameters_impl(self):
        # Get the Waveguide Type from the PCell, and update waveguide parameters
        self.waveguide_params = [t for t in self.waveguide_types if t['name'] == self.waveguide_type]
        if not self.waveguide_params:
            raise Exception ('Waveguides.XML not correctly configured')
        self.waveguide_params = self.waveguide_params [0]
        self.radius = float(self.waveguide_params['radius'])

        # We employ coerce_parameters_impl to decide whether the handle or the 
        # numeric parameters have changed. We update the 
        # numerical value or the shape, depending on which on has not changed.
        w = None
        if isinstance(self.box, pya.Box): 
            w = self.box.right*self.layout.dbu
            print('%s Box: width %s ' %(self.cellName,w))
        if isinstance(self.box, pya.DBox): 
            w = self.box.right
            print('%s DBox: width %s ' %(self.cellName,w))
        if w != None and abs(self.length-self.length1) < 1e-6:
            if w < self.minlength:
                w = self.minlength
            print('%s update from GUI Box: %s ' %(self.cellName,w))
            self.length = w
            self.length1 = w
        else:
            print('%s update from PCell parameters: %s ' %(self.cellName,self.length1))
            self.length = self.length1
        self.box = pya.DBox(-self.length,-self.minlength/2,self.length,self.minlength/2)
                    

    def can_create_from_shape_impl(self):
        return self.shape.is_box()

    def transformation_from_shape_impl(self):
        # Implement the "Create PCell from shape" protocol: we use the center of the shape's
        # bounding box to determine the transformation
        return pya.Trans(self.shape.bbox().center())

    def parameters_from_shape_impl(self):
        # self.path = self.shape.path
        # Implement the "Create PCell from shape" protocol: we set r and l from the shape's 
        # bounding box width and layer
        self.width = self.shape.bbox().width() * self.layout.dbu
        self.height = self.shape.bbox().height() * self.layout.dbu
    
    def produce_impl(self):
        self.layout.technology_name = self.technology_name
    
        from SiEPIC.utils import get_technology_by_name, load_Waveguides_by_Tech
    
        # DevRec width
        if ('DevRec' not in [wg['layer'] for wg in self.waveguide_params['component']]):
            from SiEPIC import _globals
            devrec = max([float(wg['width']) for wg in self.waveguide_params['component']]) + _globals.WG_DEVREC_SPACE * 2
        else:
            devrec = float([f for f in self.waveguide_params['component'] if f['layer']=='DevRec'][0]['width'])

        # Radius
        radius = float(self.waveguide_params['radius'])

        # SBend offset in the middle of the spiral
        if 'sbends' in self.waveguide_params:
            # Use the Bezier S-Bend (more space efficient)
            # if sbends=True in Waveguide.xml
            offset = radius - devrec/2  
            extra = 0
        else:
            # Use 2 x 90 degree bends
            offset = radius
            extra = devrec
    
        # Ensure the length is sufficient
        self.minlength = 2*radius
        length0 = max(self.minlength, self.length)  
    
        # spiral points    
        points = [DPoint(-length0,offset), DPoint(0.0,offset), DPoint(0.0,-offset), DPoint(length0,-offset)]
        for i in range(1,self.loops*2,2):
            points.insert(0, DPoint(-length0-devrec*(i-1),offset-radius*2-devrec*(i-1)-extra))
            points.insert(0, DPoint(length0+devrec*i,offset-radius*2-devrec*(i-1)-extra))
            points.insert(0, DPoint(length0+devrec*i,-offset+radius*2+devrec*i+extra))
            points.insert(0, DPoint(-length0-devrec*(i+1),-offset+radius*2+devrec*i+extra))
            points.append(DPoint(length0+devrec*(i-1),radius*2-offset+devrec*(i-1)+extra))
            points.append(DPoint(-length0-devrec*i,radius*2-offset+devrec*(i-1)+extra))
            points.append(DPoint(-length0-devrec*i,-radius*2+offset-devrec*i-extra))
            points.append(DPoint(length0+devrec*(i+1),-radius*2+offset-devrec*i-extra))
        points.append(DPoint(length0+devrec*(i+1),radius*2-offset+devrec*(i+1)+extra))
        points.append(DPoint(-length0-devrec*(i),radius*2-offset+devrec*(i+1)+extra))
        points.pop(0)
        points.insert(0, DPoint(-length0-devrec*(i),-offset+radius*2+devrec*i+extra))

        # Create a path and waveguide    
        path  = DPath(points, 0.5)
        pcell = self.layout.create_cell("Waveguide", self.technology_name, 
                    {"path": path,
                     "waveguide_type": self.waveguide_type})
        t = Trans(Trans.R0, 0, 0)
        self.cell.insert(CellInstArray(pcell.cell_index(), t))


# Save the path, used for loading WAVEGUIDES.XML
import os
filepath = os.path.dirname(os.path.realpath(__file__))


class test_lib(Library):
  def __init__(self):  
    tech = 'EBeam'
    library = tech + 'test_lib'
    self.technology=tech
    self.layout().register_pcell('spiral_paperclip', spiral_paperclip())
    self.register(library)
 
if __name__ == "__main__":
    print('Test layout for: Spiral Paperclip')
    
    from SiEPIC.utils.layout import new_layout, floorplan
    from SiEPIC.scripts import zoom_out
    
    tech = 'EBeam'

    # Create a new layout for the chip floor plan   
    topcell, ly = new_layout(tech, "test", GUI = True, overwrite = True)
    #floorplan(topcell, 100e3, 100e3)
    
    # load the test library
    t = test_lib()
    print(t.technology)
    
    # instantiate the cell
    library = tech + 'test_lib'
    pcell = ly.create_cell("spiral_paperclip", library, 
                    {
                    })
    t = Trans(Trans.R0, 0, 0)
    topcell.insert(CellInstArray(pcell.cell_index(), t))
      
    zoom_out(topcell)
