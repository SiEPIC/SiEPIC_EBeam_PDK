import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
from pya import Text, Trans, Point

from SiEPIC._globals import Python_Env
if Python_Env == 'Script':
    # For external Python mode, when installed using pip install siepic_ebeam_pdk
    import siepic_ebeam_pdk

from SiEPIC.utils.layout import new_layout, make_pin
from SiEPIC.extend import to_itype
from SiEPIC.utils import arc_wg


class Waveguide_Arc(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the waveguide arc.

    Author: Mustafa Hammood     mustafa@siepic.com
    """

    def __init__(self):
        # Important: initialize the super class
        super(Waveguide_Arc, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("radius", self.TypeDouble, "Radius", default=10)
        self.param("wg_width", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("start_angle", self.TypeDouble, "Start Angle", default=0)
        self.param("stop_angle", self.TypeDouble, "Stop Angle", default=180)
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        # hidden parameters, can be used to query this component:
        self.param(
            "p1",
            self.TypeShape,
            "DPoint location of pin1",
            default=Point(-10000, 0),
            hidden=True,
            readonly=True,
        )
        self.param(
            "p2",
            self.TypeShape,
            "DPoint location of pin2",
            default=Point(0, 10000),
            hidden=True,
            readonly=True,
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Waveguide_Arc(R=" + ("%.3f" % self.radius) + ")"

    def produce(self, layout, layers, parameters, cell):
        """
        coerce parameters (make consistent)
        """
        self._layers = layers
        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        # cell: layout cell to place the layout
        # LayerSiN: which layer to use
        # r: radius
        # w: waveguide width
        # start_angle: starting angle of the arc
        # stop_agnle: stopping angle of the arc
        # length units in dbu
        import math

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = self.silayer
        LayerSiN = self.silayer_layer
        #    LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)


        w = to_itype(self.wg_width, dbu)
        r = to_itype(self.radius, dbu)
        start_angle = self.start_angle
        stop_angle = self.stop_angle

        if start_angle > stop_angle:
            start_angle = self.stop_angle
            stop_angle = self.start_angle

        deg_to_rad = math.pi / 180.0

        # draw the arc waveguide
        x = 0
        y = 0
        wg_polygon = arc_wg(r, w, start_angle, stop_angle)
        self.cell.shapes(LayerSiN).insert(wg_polygon)
        waveguide_length = wg_polygon.area()/w
        
        # Create the pins, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        # Pin on the right side:
        x = r * math.cos(start_angle * deg_to_rad)
        y = r * math.sin(start_angle * deg_to_rad)

        x_pin = math.cos((90 - start_angle) * deg_to_rad) * pin_length / 2
        y_pin = math.sin((90 - start_angle) * deg_to_rad) * pin_length / 2

        p2 = [Point(x - x_pin, y + y_pin), Point(x + x_pin, y - y_pin)]
        p2c = Point(x, y)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x, y)
        text = Text("pin2", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin on the left side:
        x = round(r * math.cos(stop_angle * deg_to_rad))
        y = round(r * math.sin(stop_angle * deg_to_rad))

        x_pin = math.cos((90.0 - stop_angle) * deg_to_rad) * pin_length / 2
        y_pin = math.sin((90.0 - stop_angle) * deg_to_rad) * pin_length / 2

        p1 = [Point(x + x_pin, y - y_pin), Point(x - x_pin, y + y_pin)]
        p1c = Point(x, y)
        self.set_p1 = p1c
        self.p1 = p1c
        pin = Path(p1, w)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x, y)
        text = Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        x = 0
        y = 0
        # layout_arc_wg_dbu(self.cell, LayerDevRecN, x, y, r, w*3, start_angle, stop_angle)
        self.cell.shapes(LayerDevRecN).insert(arc_wg(r, w * 3, start_angle, stop_angle))


        # Compact model information
        t = pya.Trans(pya.Trans.R0, r, 0)
        text = Text("Lumerical_INTERCONNECT_library=EBeam", t, w/10, -1)
        shape = self.cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = w / 10
        t = pya.Trans(pya.Trans.R0, r, w / 4)
        text = pya.Text("Component=ebeam_wg_integral_1550", t, w/10, -1)
        shape = self.cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = w / 10
        t = pya.Trans(pya.Trans.R0, r, w / 2)
        text = Text(
            "Spice_param:wg_length=%.3fu wg_width=%.3fu"
            % (waveguide_length * dbu, w*dbu), t, w / 10, -1
        )
        shape = self.cell.shapes(LayerDevRecN).insert(text)
        



class test_lib(pya.Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("Waveguide_Arc", Waveguide_Arc())
        self.register(library)

if __name__ == "__main__":
    print("Test layout for: Waveguide_Arc")

    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout for the chip floor plan
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)

    # instantiate the cell
    library = tech + "test_lib"

    # Create spirals for all the types of waveguides
    from SiEPIC.utils import load_Waveguides_by_Tech

    waveguide_types = load_Waveguides_by_Tech(tech)
    technology = get_technology_by_name('EBeam')
    xmax = 0
    y = 0
    x = xmax
    pcell = ly.create_cell(
        "Waveguide_Arc",
        library,{})
    t = pya.Trans(pya.Trans.R0, x, y - pcell.bbox().bottom)
    inst = topcell.insert(pya.CellInstArray(pcell.cell_index(), t))

    # Display in KLayout, saving the layout in the PCell's folder
    import os
    topcell.show(os.path.dirname(__file__))
