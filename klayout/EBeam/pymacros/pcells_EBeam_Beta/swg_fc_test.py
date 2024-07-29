import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
from SiEPIC.utils import points_per_circle  # ,layout


class swg_fc_test(pya.PCellDeclarationHelper):
    """
    Sub-wavelength-grating fibre coupler PCell litho test structure.

    2017/07/12: Lukas Chrostowski, initial version, based on swg_fc by Tim

    Input:

    """

    def __init__(self):
        # Important: initialize the super class
        super(swg_fc_test, self).__init__()

        # declare the parameters
        self.param(
            "wavelength", self.TypeDouble, "Design Wavelength (micron)", default=2.9
        )
        self.param("n_t", self.TypeDouble, "Fiber Mode", default=1.0)
        self.param("n_e", self.TypeDouble, "Grating Index Parameter", default=3.1)
        self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default=20.0)
        self.param(
            "grating_length", self.TypeDouble, "Grating Length (micron)", default=3.0
        )
        self.param(
            "taper_length", self.TypeDouble, "Taper Length (micron)", default=32.0
        )
        self.param("dc", self.TypeDouble, "Duty Cycle", default=0.488193)
        self.param("period", self.TypeDouble, "Grating Period", default=1.18939)
        self.param("ff", self.TypeDouble, "Fill Factor", default=0.244319)
        self.param("t", self.TypeDouble, "Waveguide Width (micron)", default=1.0)
        self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default=8.0)
        self.param(
            "fab_error", self.TypeDouble, "Fab Process error max (micron)", default=0.05
        )

        # Layer parameters
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "swg_fc_test_%.1f-%.2f-%.2f-%.2f-%.2f-%.2f-%.2f-%.2f" % (
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
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)

        from math import pi, cos, sin

        lambda_0 = self.wavelength  ##um wavelength of light
        pin_length = 0.5  ##um extra nub for the waveguid attachment

        # Geometry
        wh = self.period * self.dc  ##thick grating
        wl = self.ff * (self.period - wh)  ## thin grating
        spacing = (self.period - wh - wl) / 2  ##space between thick and thin

        gc_number = int(round(self.grating_length / self.period))  ##number of periods
        gc_number = 3
        e = self.n_t * sin((pi / 180) * self.theta_c) / self.n_e
        N = round(
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
            rng = range(len(theta_up))

            # find the divider to get desired fab error:
            th = min(theta_up)
            div = (2 * sin(th) / self.fab_error) * (
                N * lambda_0 / (self.n_e * (1 - e * cos(th)))
                + j * self.period
                + spacing
            )
            err = (2 * sin(th) / div) * (
                N * lambda_0 / (self.n_e * (1 - e * cos(th)))
                + j * self.period
                + spacing
            )
            #        print("div %s, err (double check) %s" % (div, err))

            for k in rng:
                th = theta_up[k]
                #          print("%s, %s, %s" % (th, sin(th), 1+sin(th)/10.) )
                r_up = r_up + [
                    (1 - sin(th) / div)
                    * (
                        N * lambda_0 / (self.n_e * (1 - e * cos(th)))
                        + j * self.period
                        + spacing
                    )
                ]
            for k in rng[::-1]:
                th = theta_up[k]
                #          print("%s, %s, %s" % (th, sin(th), 1+sin(th)/10.) )
                r_down = r_down + [
                    (1 + sin(th) / div)
                    * (
                        N * lambda_0 / (self.n_e * (1 - e * cos(th)))
                        + j * self.period
                        + spacing
                    )
                ]

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
                pts.append(Point.from_dpoint(pya.DPoint(x[i] / dbu, y[i] / dbu)))
            # small_one = core.Boundary(points)

            polygon = Polygon(pts)
            shapes(LayerSiN).insert(polygon)

            if j == 1:
                # text label dimensions, for minor grating:
                # top
                shapes(LayerTextN).insert(
                    Text(
                        "%0.0f" % ((wl + self.fab_error) * 1000),
                        Trans(Trans.R0, xl[0] / dbu, yl[0] / dbu),
                    )
                ).text_size = 0.2 / dbu
                # btm
                shapes(LayerTextN).insert(
                    Text(
                        "%0.0f" % ((wl - self.fab_error) * 1000),
                        Trans(Trans.R0, xl[-1] / dbu, yl[-1] / dbu),
                    )
                ).text_size = 0.2 / dbu
                # mid
                shapes(LayerTextN).insert(
                    Text(
                        "%0.0f" % ((wl) * 1000),
                        Trans(
                            Trans.R0,
                            xl[int(len(theta_up) / 2)] / dbu,
                            yl[int(len(theta_up) / 2)] / dbu,
                        ),
                    )
                ).text_size = 0.2 / dbu

            ##big one
            r_up = []
            r_down = []

            # find the divider to get desired fab error:
            th = min(theta_up)
            div = (2 * sin(th) / self.fab_error) * (
                N * lambda_0 / (self.n_e * (1 - e * cos(th)))
                + j * self.period
                + 2 * spacing
                + wl
            )
            err = (2 * sin(th) / div) * (
                N * lambda_0 / (self.n_e * (1 - e * cos(th)))
                + j * self.period
                + 2 * spacing
                + wl
            )
            #        print("div %s, err (double check) %s" % (div, err))

            rng = range(len(theta_up))
            for k in rng:
                th = theta_up[k]
                r_up = r_up + [
                    (1 - sin(th) / div)
                    * (
                        N * lambda_0 / (self.n_e * (1 - e * cos(th)))
                        + j * self.period
                        + 2 * spacing
                        + wl
                    )
                ]
            for k in rng[::-1]:
                th = theta_up[k]
                r_down = r_down + [
                    (1 + sin(th) / div)
                    * (
                        N * lambda_0 / (self.n_e * (1 - e * cos(th)))
                        + j * self.period
                        + 2 * spacing
                        + wl
                    )
                ]

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
                pts.append(Point.from_dpoint(pya.DPoint(x[i] / dbu, y[i] / dbu)))

            polygon = Polygon(pts)
            shapes(LayerSiN).insert(polygon)

            if j == 1:
                # text label dimensions, for major grating:
                # top
                shapes(LayerTextN).insert(
                    Text(
                        "%0.0f" % ((wh + self.fab_error) * 1000),
                        Trans(Trans.R0, xl[0] / dbu, yl[0] / dbu),
                    )
                ).text_size = 0.2 / dbu
                # btm
                shapes(LayerTextN).insert(
                    Text(
                        "%0.0f" % ((wh - self.fab_error) * 1000),
                        Trans(Trans.R0, xl[-1] / dbu, yl[-1] / dbu),
                    )
                ).text_size = 0.2 / dbu
                # mid
                shapes(LayerTextN).insert(
                    Text(
                        "%0.0f" % ((wh) * 1000),
                        Trans(
                            Trans.R0,
                            xl[int(len(theta_up) / 2)] / dbu,
                            yl[int(len(theta_up) / 2)] / dbu,
                        ),
                    )
                ).text_size = 0.2 / dbu
