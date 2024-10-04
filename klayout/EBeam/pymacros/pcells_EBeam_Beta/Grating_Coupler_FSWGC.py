import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Grating_Coupler_FSWGC(pya.PCellDeclarationHelper):
    """
    Focusing Sub-wavelength grating coupler PCell implementation.
    Analytical design based on "Grating Coupler Design Based on Silicon-On-Insulator", Yun Wang (2013). Master's Thesis, University of British Columbia, Canada
    Some PCell implementation adapted from the SiEPIC_EBeam library by Dr. Lukas Chrostowski, University of British Columbia, Canada

    Separate modelling (e.g. Lumerical MODE) is required to determine the "grating effective index" parameter for a given device layer thickness,
    cladding type, and period/duty cycle/fill factor.

    Script written by Timothy Richards (Simon Fraser University, BC, Canada) and Adam DeAbreu (Simon Fraser University, BC, Canada)

    Changelog

    2017-07-07 - initial publish
    2017-07-07 - change library & component names; commit to github

    TO-DO:
    - implement mode solver here, or call Lumerical MODE to calculate
    - needs to be verified experimentally
    - default parameters are not correct; compare with "ebeam_gc_te1550"

    Input:

    """

    def __init__(self):
        # Important: initialize the super class
        super(Grating_Coupler_FSWGC, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param(
            "wavelength", self.TypeDouble, "Design Wavelength (micron)", default=1.55
        )
        self.param("n_t", self.TypeDouble, "Cladding Index", default=1.0)
        self.param("n_e", self.TypeDouble, "Grating Effective Index", default=2.75618)
        self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default=35.0)
        self.param(
            "grating_length", self.TypeDouble, "Grating Length (micron)", default=15.0
        )
        self.param(
            "taper_length", self.TypeDouble, "Taper Length (micron)", default=19.0
        )
        self.param("dc", self.TypeDouble, "Duty Cycle", default=0.488193)
        self.param("period", self.TypeDouble, "Grating Period", default=1.18939)
        self.param("ff", self.TypeDouble, "Fill Factor", default=0.244319)
        self.param("t", self.TypeDouble, "Waveguide Width (micron)", default=0.5)
        self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default=-31.0)

        # Layer parameters
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Grating_Coupler_FSWGC_%.1f-%.2f-%.2f-%.2f-%.2f-%.2f-%.2f-%.2f" % (
            self.wavelength,
            self.theta_c,
            self.period,
            self.dc,
            self.ff,
            self.angle_e,
            self.taper_length,
            self.t,
        )

    #    return "temporary placeholder"

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerSiSPN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        from math import pi, cos, sin, tan
        from SiEPIC.utils import points_per_circle

        lambda_0 = self.wavelength  ##um wavelength of light
        #    pin_length =0.0                 ##um extra nub for the waveguide attachment

        # Geometry
        wh = self.period * self.dc  ##thick grating
        wl = self.ff * (self.period - wh)  ## thin grating
        spacing = (self.period - wh - wl) / 2  ##space between thick and thin

        gc_number = int(round(self.grating_length / self.period))  ##number of periods
        e = self.n_t * sin((pi / 180) * self.theta_c) / self.n_e
        N = (
            self.taper_length * (1 + e) * self.n_e / lambda_0
        )  ##allows room for the taper

        start = pi - (pi / 180) * self.angle_e / 2
        stop = pi + (pi / 180) * self.angle_e / 2

        # Draw coupler grating.
        for j in range(gc_number):
            # number of points in the arcs:
            # calculate such that the vertex & edge placement error is < 0.5 nm.
            #   see "SiEPIC_EBeam_functions - points_per_circle" for more details
            radius = N * lambda_0 / (self.n_e * (1 - e)) + j * self.period + spacing
            seg_points = int(
                points_per_circle(radius / dbu) / 360.0 * self.angle_e
            )  # number of points grating arc
            theta_up = []
            for m in range(seg_points + 1):
                theta_up = theta_up + [start + m * (stop - start) / seg_points]
            theta_down = theta_up[::-1]

            ##small one
            r_up = []
            r_down = []
            for k in range(len(theta_up)):
                r_up = r_up + [
                    N * lambda_0 / (self.n_e * (1 - e * cos(float(theta_up[k]))))
                    + j * self.period
                    + spacing
                ]
            r_down = r_up[::-1]

            xr = []
            yr = []
            for k in range(len(theta_up)):
                xr = xr + [r_up[k] * cos(theta_up[k])]
                yr = yr + [r_up[k] * sin(theta_up[k])]

            xl = []
            yl = []
            for k in range(len(theta_down)):
                xl = xl + [(r_down[k] + wl) * cos(theta_down[k])]
                yl = yl + [(r_down[k] + wl) * sin(theta_down[k])]

            x = xr + xl
            y = yr + yl

            pts = []
            for i in range(len(x)):
                pts.append(Point.from_dpoint(DPoint(x[i] / dbu, y[i] / dbu)))
            # small_one = core.Boundary(points)

            polygon = Polygon(pts)
            if self.ff > 0:
                shapes(LayerSiN).insert(polygon)

            ##big one
            r_up = []
            r_down = []
            for k in range(len(theta_up)):
                r_up = r_up + [
                    N * lambda_0 / (self.n_e * (1 - e * cos(float(theta_up[k]))))
                    + j * self.period
                    + 2 * spacing
                    + wl
                ]
            r_down = r_up[::-1]

            xr = []
            yr = []
            for k in range(len(theta_up)):
                xr = xr + [r_up[k] * cos(theta_up[k])]
                yr = yr + [r_up[k] * sin(theta_up[k])]

            xl = []
            yl = []
            for k in range(len(theta_down)):
                xl = xl + [(r_down[k] + wh) * cos(theta_down[k])]
                yl = yl + [(r_down[k] + wh) * sin(theta_down[k])]

            x = xr + xl
            y = yr + yl

            pts = []
            for i in range(len(x)):
                pts.append(Point.from_dpoint(DPoint(x[i] / dbu, y[i] / dbu)))

            polygon = Polygon(pts)
            shapes(LayerSiN).insert(polygon)

        # Taper section
        r_up = []
        r_down = []
        for k in range(len(theta_up)):
            r_up = r_up + [
                N * lambda_0 / (self.n_e * (1 - e * cos(float(theta_up[k]))))
            ]
        r_down = r_up[::-1]

        xl = []
        yl = []
        for k in range(len(theta_down)):
            xl = xl + [(r_down[k]) * cos(theta_down[k])]
            yl = yl + [(r_down[k]) * sin(theta_down[k])]

        yr = [self.t / 2.0, self.t / 2.0, -self.t / 2.0, -self.t / 2.0]

        yl_abs = []
        for k in range(len(yl)):
            yl_abs = yl_abs + [abs(yl[k])]

        y_max = max(yl_abs)
        iy_max = yl_abs.index(y_max)

        L_o = (y_max - self.t / 2) / tan((pi / 180) * self.angle_e / 2)

        xr = [L_o + xl[iy_max], 0, 0, L_o + xl[iy_max]]

        x = xr + xl
        y = yr + yl

        pts = []
        for i in range(len(x)):
            pts.append(Point.from_dpoint(DPoint(x[i] / dbu, y[i] / dbu)))

        polygon = Polygon(pts)
        shapes(LayerSiN).insert(polygon)

        # Pin on the waveguide:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        x = 0
        t = Trans(Trans.R0, x, 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], self.t / dbu)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Device recognition layer
        yr = sin(start) * (
            N * lambda_0 / (self.n_e * (1 - e * cos(float(start))))
            + gc_number * self.period
            + spacing
        )
        box1 = Box(
            -(self.grating_length + self.taper_length) / dbu - pin_length * 2,
            yr / dbu,
            0,
            -yr / dbu,
        )
        shapes(LayerDevRecN).insert(box1)
