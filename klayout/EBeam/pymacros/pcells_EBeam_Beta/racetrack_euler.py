'''
Racetrack resonator using Euler bends

by Lukas Chrostowski
using Euler bends implemented by Evan Jonker

'''


import pya
from pya import *
from pya import Text

import SiEPIC
from packaging import version
if version.parse(SiEPIC.__version__) < version.parse("0.5.11"):
    raise Exception(
        "Errors",
        "This PCell requires SiEPIC-Tools version 0.5.11 or greater. You have %s"
        % SiEPIC.__version__,
    )
from SiEPIC.utils import get_technology_by_name
from SiEPIC.utils.layout import make_pin

class racetrack_euler(pya.PCellDeclarationHelper):
    """
    A racetrack resonator using Euler curve for the U-turn.
    """

    def __init__(self):
        # Important: initialize the super class
        super(racetrack_euler, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # Button to launch separate window
        self.param(
            "documentation", self.TypeCallback, "Open documentation in web browser"
        )
        #    self.param("simulation", self.TypeCallback, "Launch simulation GUI")

        # declare the parameters
        self.param("w", self.TypeDouble, "Waveguide Width (micron)", default=0.5)
        self.param("g", self.TypeDouble, "Coupler Gap (micron)", default=0.7)
        self.param("Lc", self.TypeDouble, "Coupler Length (micron)", default=151)
        self.param("r", self.TypeDouble, "Effective Bend Radius (micron)", default=5)
        self.param("p", self.TypeDouble, "Euler parameter, p", default=0.25)
        self.param("silayer", self.TypeLayer, "Waveguide Layer", default=TECHNOLOGY["Si"])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"])

    def callback(self, layout, name, states):
        """Callback for PCell, to launch documentation viewer
        https://www.klayout.de/doc/code/class_PCellDeclaration.html#method9
        """
        if name == "documentation":
            url = "https://github.com/SiEPIC/SiEPIC_EBeam_PDK"
            import webbrowser

            webbrowser.open_new(url)

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "racetrack_euler("
            + (
                "%.3f-%.3f-%.3f-%.3f-%.3f"
                % (self.w, self.Lc, self.g, self.r, self.p)
            )
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce(self, layout, layers, parameters, cell):

        self._layers = layers
        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        ly.technology_name = 'EBeam'

        LayerSi = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Bends in the racetrack
        y = self.g+self.w


        # Bends in the racetrack
        pcell = ly.create_cell("euler_bend_180", "EBeam_Beta", {
                "p": self.p,
                "ww": self.w,
                "radius": self.r,
                "shape_only": True,         
        })
        t = pya.Trans(pya.Trans.R0, self.Lc/2/dbu, y/dbu)
        inst = cell.insert(pya.CellInstArray(pcell.cell_index(), t))
        t = pya.Trans(pya.Trans.R180, -self.Lc/2/dbu, (self.r*2+y)/dbu)
        inst = cell.insert(pya.CellInstArray(pcell.cell_index(), t))


        # straight waveguides in the racetrack
        wg = pya.DBox(-self.Lc/2,-self.w/2+y, self.Lc/2, self.w/2+y)
        cell.shapes(LayerSi).insert(wg)
        cell.shapes(LayerSi).insert(wg.transformed(pya.Trans(pya.Trans.R0,0,self.r*2)))

        # bus waveguide
        wg = pya.DBox(-self.Lc/2-self.r*2,-self.w/2, self.Lc/2+self.r*2, self.w/2)
        cell.shapes(LayerSi).insert(wg)
        

        # Create the pins on the waveguides, as short paths:
        make_pin(self.cell, "opt1", [-self.Lc/2-self.r*2, 0], self.w, LayerPinRecN, 180)
        make_pin(self.cell, "opt2", [self.Lc/2+self.r*2, 0], self.w, LayerPinRecN, 0)

        
        # Create the device recognition layer
        box = pya.DBox(-self.Lc/2-self.r*2,-self.w*3/2, self.Lc/2+self.r*2, y+self.r*2+self.w*2)
        cell.shapes(LayerDevRecN).insert(box)


        '''


        # Compact model information
        t = pya.Trans(pya.Trans.R0, w1 / 10, 0)
        text = Text("Lumerical_INTERCONNECT_library=None", t)
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = pya.Trans(pya.Trans.R0, length / 10, w1 / 4)
        text = pya.Text("Component=racetrack_bezier", t)
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = pya.Trans(pya.Trans.R0, length / 10, w1 / 2)
        text = pya.Text(
            "Spice_param:w=%.3fu g=%.3fu Lc=%.3fu"
            % (self.w, self.g, self.Lc),
            t,
        )
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        '''
        
        return (
            "racetrack_euler("
            + ("%.3f-%.3f-%.3f" % (self.w, self.Lc, self.g))
            + ")"
        )


class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("racetrack_euler", racetrack_euler())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: racetrack_euler")

    import siepic_ebeam_pdk
    from SiEPIC.utils.layout import new_layout

    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout for the chip floor plan
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)

    # instantiate the cell
    library = tech + "test_lib"

    # Create for several combinations
    # 3e8/2/4.4/340e-6*1e-9 = 100 GHz
    # Lc = 340/2-19, or 340/2-39
    params = [
        {"w": 0.5, "g": 0.5, "Lc": 151, "p": 0.25, "r":5}, # 19 micron long bend
        {"w": 0.5, "g": 0.6, "Lc": 131, "p": 0.3, "r":10}, # 39 micron long bend
        {"w": 0.5, "g": 0.6, "Lc": 131, "p": 0.5, "r":10}, # 39 micron long bend
    ]
    xmax = 0
    y = 0
    x = xmax
    for p in params:
        print(p)
        pcell = ly.create_cell("racetrack_euler", library, p)
        t = pya.Trans(pya.Trans.R0, x, y - pcell.bbox().bottom)
        inst = topcell.insert(pya.CellInstArray(pcell.cell_index(), t))
        y += pcell.bbox().height() + 2000
        xmax = max(xmax, x + inst.bbox().width())

    # Display in KLayout, saving the layout in the PCell's folder
    import os
    topcell.show(os.path.dirname(__file__))
