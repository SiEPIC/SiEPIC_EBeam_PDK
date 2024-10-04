import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class taper_bezier(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the strip waveguide taper using Bezier curve.
    """

    def __init__(self):
        # Important: initialize the super class
        super(taper_bezier, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # Button to launch separate window
        self.param(
            "documentation", self.TypeCallback, "Open documentation in web browser"
        )
        #    self.param("simulation", self.TypeCallback, "Launch simulation GUI")

        # declare the parameters
        self.param(
            "wg_width1", self.TypeDouble, "Waveguide Width1 (micron)", default=0.5
        )
        self.param("wg_width2", self.TypeDouble, "Waveguide Width2 (micron)", default=3)
        self.param(
            "wg_length", self.TypeDouble, "Waveguide Length (micron)", default=10
        )
        self.param("a", self.TypeDouble, "Bezier parameter, a (0-1)", default=0.37)
        self.param("b", self.TypeDouble, "Bezier parameter, b (0-1)", default=0.37)
        self.param(
            "accuracy", self.TypeDouble, "Curve accuracy (micron)", default=0.005
        )
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
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

    def callback(self, layout, name, states):
        """Callback for PCell, to launch documentation viewer
        https://www.klayout.de/doc/code/class_PCellDeclaration.html#method9
        """
        if name == "documentation":
            url = "https://github.com/SiEPIC/SiEPIC_EBeam_PDK/blob/master/Documentation/Taper/Summary_Taper.pdf"
            import webbrowser

            webbrowser.open_new(url)

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "taper_bezier("
            + (
                "%.3f-%.3f-%.3f-%.3f-%.3f"
                % (self.wg_width1, self.wg_width2, self.wg_length, self.a, self.b)
            )
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce(self, layout, layers, parameters, cell):
        from packaging import version
        import SiEPIC

        if version.parse(SiEPIC.__version__) < version.parse("0.5.11"):
            raise Exception(
                "Errors",
                "This PCell requires SiEPIC-Tools version 0.5.11 or greater. You have %s"
                % SiEPIC.__version__,
            )

        from SiEPIC.utils.geometry import bezier_cubic
        from SiEPIC.extend import to_itype
        from SiEPIC.utils.layout import make_pin

        """
    coerce parameters (make consistent)
    """
        self._layers = layers
        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        w1 = to_itype(self.wg_width1, dbu)
        w2 = to_itype(self.wg_width2, dbu)
        length = to_itype(self.wg_length, dbu)

        wg_Dpts = (
            bezier_cubic(
                pya.DPoint(0, self.wg_width1 / 2),
                pya.DPoint(self.wg_length, self.wg_width2 / 2),
                0,
                0,
                self.a,
                self.b,
                accuracy=self.accuracy,
            )
            + bezier_cubic(
                pya.DPoint(0, -self.wg_width1 / 2),
                pya.DPoint(self.wg_length, -self.wg_width2 / 2),
                0,
                0,
                self.a,
                self.b,
                accuracy=self.accuracy,
            )[::-1]
        )
        wg_polygon = pya.DPolygon(wg_Dpts)
        cell.shapes(LayerSi).insert(wg_polygon)

        # Create the pins on the waveguides, as short paths:
        make_pin(self.cell, "opt1", [0, 0], w1, LayerPinRecN, 180)
        make_pin(self.cell, "opt2", [length, 0], w2, LayerPinRecN, 0)

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        path = pya.Path([pya.Point(0, 0), pya.Point(length, 0)], w2 + w1 * 2)
        cell.shapes(LayerDevRecN).insert(path.simple_polygon())

        # Compact model information
        t = pya.Trans(pya.Trans.R0, w1 / 10, 0)
        text = Text("Lumerical_INTERCONNECT_library=None", t)
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = pya.Trans(pya.Trans.R0, length / 10, w1 / 4)
        text = pya.Text("Component=taper_bezier", t)
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = pya.Trans(pya.Trans.R0, length / 10, w1 / 2)
        text = pya.Text(
            "Spice_param:wg_width1=%.3fu wg_width2=%.3fu wg_length=%.3fu"
            % (self.wg_width1, self.wg_width2, self.wg_length),
            t,
        )
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100

        return (
            "taper_bezier("
            + ("%.3f-%.3f-%.3f" % (self.wg_width1, self.wg_width2, self.wg_length))
            + ")"
        )


class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("taper_bezier", taper_bezier())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: Taper Bezier")

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
    params = [
        {"wg_width1": 0.5, "wg_width2": 1, "wg_length": 10, "a": 0.37, "b": 0.37},
        {"wg_width1": 0.5, "wg_width2": 2, "wg_length": 20, "a": 0.37, "b": 0.37},
        {"wg_width1": 0.5, "wg_width2": 3, "wg_length": 10, "a": 0.37, "b": 0.37},
        {"wg_width1": 0.5, "wg_width2": 3, "wg_length": 20, "a": 0.37, "b": 0.37},
        {"wg_width1": 0.5, "wg_width2": 3, "wg_length": 20, "a": 0.2, "b": 0.2},
        {"wg_width1": 0.5, "wg_width2": 3, "wg_length": 20, "a": 0.7, "b": 0.7},
        {"wg_width1": 0.5, "wg_width2": 3, "wg_length": 20, "a": 0.7, "b": 0.3},
        {"wg_width1": 0.5, "wg_width2": 3, "wg_length": 40, "a": 0.37, "b": 0.37},
    ]
    xmax = 0
    y = 0
    x = xmax
    for p in params:
        print(p)
        pcell = ly.create_cell("taper_bezier", library, p)
        t = pya.Trans(pya.Trans.R0, x, y - pcell.bbox().bottom)
        inst = topcell.insert(pya.CellInstArray(pcell.cell_index(), t))
        y += pcell.bbox().height() + 2000
        xmax = max(xmax, x + inst.bbox().width())

    # Save
    import os
    from SiEPIC.scripts import export_layout

    path = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.splitext(os.path.basename(__file__))[0]
    file_out = export_layout(topcell, path, filename, format="oas", screenshot=True)

    # Display in KLayout
    from SiEPIC._globals import Python_Env

    if Python_Env == "Script":
        from SiEPIC.utils import klive

        klive.show(file_out, technology=tech, keep_position=True)
