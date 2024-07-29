import pya
from . import *
from pya import *


class Waveguide_bump(pya.PCellDeclarationHelper):
    """
    Create a waveguide with a "bump" consisting of four bends,
    to implement an extra length as compared to a straight waveguide.
    Input:
     - delta_length
     - waveguide_type from Waveguides.XML
    Calculates the theta for the four arcs
    Uses waveguide parameters
    Increases the bend radius in case of Bezier curves
    """

    def __init__(self):
        # Important: initialize the super class
        super(Waveguide_bump, self).__init__()
        from SiEPIC.utils import get_technology_by_name, load_Waveguides_by_Tech

        TECHNOLOGY = get_technology_by_name("EBeam")
        self.technology_name = "EBeam"

        # Load all waveguides types
        self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)

        # find SiN waveguide
        names = [w["name"] for w in self.waveguide_types if "SiN" in w["name"]]
        if not names:
            raise Exception("Waveguides.XML does not have a SiN waveguide.")

        # declare the parameters
        p = self.param(
            "waveguide_type", self.TypeList, "Waveguide Type", default=names[0]
        )
        for wa in self.waveguide_types:
            p.add_choice(wa["name"], wa["name"])

        # declare the parameters
        self.param(
            "delta_length", self.TypeDouble, "Waveguide length difference", default=0.2
        )
        self.param("max_theta", self.TypeDouble, "Maximum angle (degrees)", default=149)
        self.param(
            "radius_mult",
            self.TypeDouble,
            "Waveguide radius multiplier for Bezier bends",
            default=2,
        )
        self.param(
            "radius",
            self.TypeDouble,
            "Waveguide Radius (microns)",
            default=self.waveguide_types[0]["radius"],
            readonly=True,
        )
        self.param(
            "wg_width",
            self.TypeDouble,
            "Waveguide width (microns)",
            default=0.5,
            readonly=True,
        )
        self.param(
            "theta",
            self.TypeDouble,
            "Waveguide angle (degrees)",
            default=5,
            hidden=True,
        )
        self.param(
            "length",
            self.TypeDouble,
            "Regular Waveguide length",
            default=10.0,
            hidden=True,
        )

        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("text", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Waveguide_bump_%s-%.3f" % (self.length, self.wg_width)

    def coerce_parameters_impl(self):
        params = [t for t in self.waveguide_types if t["name"] == self.waveguide_type]
        if not params:
            raise Exception("Waveguides.XML not correctly configured")

        if "bezier" in params[0]:
            # chose a radius that is larger to avoid loss
            mult = self.radius_mult
        else:
            mult = 1
        self.radius = float(params[0]["radius"]) * mult
        self.wg_width = float(params[0]["width"])

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        from SiEPIC.utils import get_technology_by_name

        TECHNOLOGY = get_technology_by_name("EBeam")
        params = [t for t in self.waveguide_types if t["name"] == self.waveguide_type]
        layer = [wg["layer"] for wg in params[0]["component"]]
        try:
            layer.remove("DevRec")
        except:
            pass
        if not layer:
            raise Exception("Waveguides.XML not correctly configured")
        LayerSiN = ly.layer(TECHNOLOGY[layer[0]])
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.text)

        from math import pi, cos, sin
        from SiEPIC.utils import arc_wg

        x = 0
        y = 0

        from SiEPIC.extend import to_itype

        # Waveguide parameters:
        w = to_itype(self.wg_width, self.layout.dbu)
        r = to_itype(self.radius, dbu)

        # Solve for the value of theta that gives us the desired delta_length
        # four arcs with the same radius and angle
        # delta_length = waveguide_length - device length
        # delta_length = 2*pi*r*(4*theta/360.0) - 4*r*sin(theta/180.0*pi)
        """
    Code from ChatGPT:
    Lukas: I want to solve the following equation for theta, 
            given delta_length and r, using Python: 
            delta_length = 2*pi*r*(4*theta/360.0) - 4*r*sin(theta/180.0*pi)
    ChatGPT:
    To solve the equation for theta using Python, 
    you can use a numerical optimization method like the bisection method, 
    Newton's method, or the secant method. 
    Here's an example implementation using the bisection method:
    Here, the f function represents the equation we want to solve, 
    and the solve_theta function uses the bisection method to find 
    the root of this equation within a given tolerance. 
    The a and b variables represent the endpoints of the initial interval, 
    and the tol variable represents the desired tolerance for the solution.
    To use this function, you can call solve_theta with your values 
    for delta_length and r.
    This will output the value of theta that satisfies the equation. 
    Note that the solution will be in degrees, since that's the unit 
    used in the equation. If you need the solution in radians, 
    you can convert it using theta_rad = theta / 180 * math.pi.
    """

        def f(theta, delta_length, r):
            import math

            return (
                delta_length
                - 2 * math.pi * r * (4 * theta / 360.0)
                + 4 * r * math.sin(theta / 180.0 * math.pi)
            )

        def solve_theta(delta_length, r):
            a, b = 0, 180
            tol = 1e-6
            while abs(b - a) > tol:
                c = (a + b) / 2
                if f(a, delta_length, r) * f(c, delta_length, r) < 0:
                    b = c
                else:
                    a = c
            return (a + b) / 2

        theta = solve_theta(self.delta_length, r * dbu)

        # Check for angle
        if theta > self.max_theta:
            theta = self.max_theta
            self.delta_length = 2 * pi * r * dbu * (
                4 * theta / 360.0
            ) - 4 * r * dbu * sin(theta / 180.0 * pi)
            self.coerce_parameters_impl()

        # length of the waveguide and device:
        waveguide_length = 2 * pi * r * (4 * theta / 360.0)
        length = 4 * r * sin(theta / 180.0 * pi)
        delta_length = waveguide_length - length

        t = Trans(Trans.R0, x, round(y + r))
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, 270.0, 270.0 + theta, dbu=dbu).transformed(t)
        )
        t = Trans(
            Trans.R0,
            round(x + length / 2),
            round(y - r + 2 * r * (1 - cos(theta / 180.0 * pi))),
        )
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, 90.0 - theta, 90.0 + theta, dbu=dbu).transformed(t)
        )
        t = Trans(Trans.R0, round(x + length), round(y + r))
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, 270.0 - theta, 270, dbu=dbu).transformed(t)
        )

        # Create the pins on the waveguides, as short paths:
        from SiEPIC.utils.layout import make_pin

        make_pin(self.cell, "pin1", [x, y], w, LayerPinRecN, 180)
        make_pin(self.cell, "pin2", [x + length * dbu, y], w, LayerPinRecN, 0)

        # Compact model information
        t = Trans(Trans.R0, 0, 0)
        cml = params[0]["CML"]
        if cml:
            text = Text("Lumerical_INTERCONNECT_library=Design kits/%s" % cml, t)
            shape = shapes(LayerDevRecN).insert(text)
            shape.text_size = 0.1 / dbu
            t = Trans(Trans.R0, 0, w * 2)
        model = params[0]["model"]
        if model:
            text = Text("Component=%s" % model, t)
            shape = shapes(LayerDevRecN).insert(text)
            shape.text_size = 0.1 / dbu
            t = Trans(Trans.R0, 0, -w * 2)
        text = Text(
            "Spice_param:wg_length=%.3fu wg_width=%.3fu"
            % (waveguide_length * dbu, self.wg_width),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu

        t = Trans(Trans.R0, self.length / 6, -w * 2)
        text = Text("dL = %.4f um" % (delta_length * dbu), t)
        shape = shapes(LayerTextN).insert(text)
        #    shape.text_size = w*1.2
        shape.text_size = length * 0.06

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        box1 = Box(0, -w * 3, length, w * 3 + (2 * r * (1 - cos(theta / 180.0 * pi))))
        shapes(LayerDevRecN).insert(box1)

        # print("SiEPIC EBeam: Waveguide_bump complete.")
