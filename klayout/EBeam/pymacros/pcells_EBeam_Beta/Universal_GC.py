import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
from . import *


class Universal_GC(pya.PCellDeclarationHelper):
    """
    Universal Grating Coupler PCell implementation.
    Analytical design based on "Grating Coupler Design Based on Silicon-On-Insulator", Yun Wang (2013). Master's Thesis, University of British Columbia, Canada
    Some PCell implementation adapted from the SiEPIC_EBeam library by Dr. Lukas Chrostowski, University of British Columbia, Canada
    Orignal script written by Timothy Richards (Simon Fraser University, BC, Canada) and Adam DeAbreu (Simon Fraser University, BC, Canada)
    Modified to use UGC method presented in : Yun Wang, Jonas Flueckiger, Charlie Lin, Lukas Chrostowski, "Universal grating coupler design," Proc. SPIE 8915, Photonics North 2013, 89150Y (11 October 2013),
    Transfered from Mentor Graphics to KLayout by Connor Mosquera (University of British Columbia, Canada)

    """

    def __init__(self):
        # Important: initialize the super class
        super(Universal_GC, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.TECHNOLOGY = TECHNOLOGY

        # declare the parameters
        self.param(
            "wavelength", self.TypeDouble, "Design Wavelength (micron)", default=1.55
        )
        self.param(
            "Si_thickness", self.TypeDouble, "Silicon Thickness (micron)", default=0.22
        )
        self.param("etch_depth", self.TypeDouble, "Etch Depth (micron)", default=0.13)
        self.param("pol", self.TypeString, "Polarization", default="TE")
        self.param("n_t", self.TypeDouble, "Cladding Index", default=1.444)
        self.param("n_2", self.TypeDouble, "Waveguide Core Index", default=3.47)
        self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default=35.0)
        self.param(
            "grating_length", self.TypeDouble, "Grating Length (micron)", default=15.0
        )
        self.param(
            "taper_length", self.TypeDouble, "Taper Length (micron)", default=19.0
        )
        self.param("dc", self.TypeDouble, "Duty Cylce", default=0.5)
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
        return "Universal_GC_%.1f-%.2f-%.2f-%.2f-%.2f-%.2f" % (
            self.wavelength,
            self.theta_c,
            self.dc,
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
        TECHNOLOGY = self.TECHNOLOGY

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerSiSPN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = TECHNOLOGY["Text"]

        ######## effective index function ##########

        def effective_index(
            wl=self.wavelength,
            etch_depth=self.etch_depth,
            Si_thickness=self.Si_thickness,
            n_t=self.n_t,
            pol=self.pol,
            dc=self.dc,
            n_2=self.n_2,
        ):
            from math import pi, cos, sin, log, sqrt, tan
            from math import pi, tan

            point = 1001
            n_0 = n_t
            n_1 = 0
            n_3 = 1.444
            if n_2 == None:
                if self.layer == self.TECHNOLOGY["Si"]:
                    n_2 = sqrt(
                        7.9874
                        + (3.68 * pow(3.9328, 2) * pow(10, 30))
                        / (
                            pow(3.9328, 2) * pow(10, 30)
                            - pow(2 * 3.14 * 3 * pow(10, 8) / (wl * pow(10, -6)), 2)
                        )
                    )  # Silicon wavelength-dependant index of refraction
                    print(n_2)
                elif self.layer == self.TECHNOLOGY["SiN"]:
                    n_2 = 2.0
                else:
                    raise Exception("Unknown waveguide material in Universal_GC PCell")
            delta = n_0 - n_3
            t = Si_thickness
            t_slot = t - etch_depth
            k_0 = 2 * pi / wl

            b_0 = linspace_without_numpy(0, 0, point - 1)
            te_0 = linspace_without_numpy(0, 0, point - 1)
            te_1 = linspace_without_numpy(0, 0, point - 1)
            tm_0 = linspace_without_numpy(0, 0, point - 1)
            tm_1 = linspace_without_numpy(0, 0, point - 1)
            h_0 = linspace_without_numpy(0, 0, point - 1)
            q_0 = linspace_without_numpy(0, 0, point - 1)
            p_0 = linspace_without_numpy(0, 0, point - 1)
            qbar_0 = linspace_without_numpy(0, 0, point - 1)
            pbar_0 = linspace_without_numpy(0, 0, point - 1)

            # calculating neff for the silicon layer
            if delta < 0:
                n_1 = n_3
            else:
                n_1 = n_0

            for ii in range(0, point - 1):
                b_0[ii] = (
                    n_1 * k_0 + (n_2 - n_1) * k_0 / (point - 1) * ii
                )  # copied from .ample UGC: should this be point-1?

                h_0[ii] = sqrt(abs(pow(n_2 * k_0, 2) - pow(b_0[ii], 2)))
                q_0[ii] = sqrt(abs(pow(b_0[ii], 2) - pow(n_0 * k_0, 2)))
                p_0[ii] = sqrt(abs(pow(b_0[ii], 2) - pow(n_3 * k_0, 2)))

                pbar_0[ii] = pow(n_2 / n_3, 2) * p_0[ii]
                qbar_0[ii] = pow(n_2 / n_0, 2) * q_0[ii]

            # calculating neff for TE mode
            if pol == "TE":
                for ii in range(0, point - 1):
                    te_0[ii] = tan(h_0[ii] * t) - (p_0[ii] + q_0[ii]) / h_0[ii] / (
                        1 - p_0[ii] * q_0[ii] / pow(h_0[ii], 2)
                    )
                    te_1[ii] = tan(h_0[ii] * t_slot) - (p_0[ii] + q_0[ii]) / h_0[ii] / (
                        1 - p_0[ii] * q_0[ii] / pow(h_0[ii], 2)
                    )

                abs_te_0 = [abs(x) for x in te_0]
                abs_te_1 = [abs(x) for x in te_1]
                index_TE_0 = abs_te_0.index(min(abs_te_0))
                index_TE_1 = abs_te_1.index(min(abs_te_1))
                nTE_0 = b_0[index_TE_0] / k_0
                nTE_1 = b_0[index_TE_1] / k_0

                while nTE_0 < 1.5 or nTE_0 > 3:
                    abs_te_0[index_TE_0] = 100
                    index_TE_0 = abs_te_0.index(min(abs_te_0))
                    nTE_0 = b_0[index_TE_0] / k_0

                while nTE_1 < 1.5 or nTE_1 > 3:
                    abs_te_1[index_TE_1] = 100
                    index_TE_1 = abs_te_1.index(min(abs_te_1))
                    nTE_1 = b_0[index_TE_1] / k_0

                ne = dc * nTE_0 + (1 - dc) * nTE_1

            # calculating neff for TE mode
            elif pol == "TM":
                for ii in range(0, point - 1):
                    tm_0[ii] = tan(h_0[ii] * t) - (pbar_0[ii] + qbar_0[ii]) / h_0[
                        ii
                    ] / (1 - pbar_0[ii] * qbar_0[ii] / pow(h_0[ii], 2))
                    tm_1[ii] = tan(h_0[ii] * t_slot) - (pbar_0[ii] + qbar_0[ii]) / h_0[
                        ii
                    ] / (1 - pbar_0[ii] * qbar_0[ii] / pow(h_0[ii], 2))

                abs_tm_0 = [abs(x) for x in tm_0]
                abs_tm_1 = [abs(x) for x in tm_1]
                index_TM_0 = abs_tm_0.index(min(abs_tm_0))
                index_TM_1 = abs_tm_1.index(min(abs_tm_1))
                nTM_0 = b_0[index_TM_0] / k_0
                nTM_1 = b_0[index_TM_1] / k_0

                while nTM_0 < 1.5 or nTM_0 > 3:
                    abs_tm_0[index_TM_0] = 100
                    index_TM_0 = abs_tm_0.index(min(abs_tm_0))
                    nTM_0 = b_0[index_TM_0] / k_0

                while nTM_1 < 1.5 or nTM_1 > 3:
                    abs_tm_1[index_TM_1] = 100
                    index_TM_1 = abs_tm_1.index(min(abs_tm_1))
                    nTM_1 = b_0[index_TM_1] / k_0

                ne = dc * nTM_0 + (1 - dc) * nTM_1

            else:
                print("Please type TE or TM for polarization")

            return ne

        #####################################

        from math import pi, cos, sin, log, sqrt, tan
        from math import pi, cos, sin, tan
        from SiEPIC.utils import points_per_circle

        lambda_0 = self.wavelength  ##um wavelength of light

        n_e = effective_index()
        ne_fiber = 1  # effective index of the mode in the air
        period = self.wavelength / (n_e - sin(pi / 180 * self.theta_c) * ne_fiber)

        # Geometry
        wh = period * self.dc  ##thick grating

        gc_number = int(round(self.grating_length / period))  ##number of periods
        e = self.n_t * sin((pi / 180) * self.theta_c) / n_e
        N = round(
            self.taper_length * (1 + e) * n_e / lambda_0
        )  ##allows room for the taper

        start = pi - (pi / 180) * self.angle_e / 2
        stop = pi + (pi / 180) * self.angle_e / 2

        # Draw coupler grating.
        for j in range(gc_number):
            # number of points in the arcs:
            # calculate such that the vertex & edge placement error is < 0.5 nm.
            #   see "SiEPIC_EBeam_functions - points_per_circle" for more details
            radius = N * lambda_0 / (n_e * (1 - e)) + j * period
            seg_points = int(
                points_per_circle(radius / dbu) / 360.0 * self.angle_e
            )  # number of points grating arc
            theta_up = []
            for m in range(seg_points + 1):
                theta_up = theta_up + [start + m * (stop - start) / seg_points]
            theta_down = theta_up[::-1]

            ##big one
            r_up = []
            r_down = []
            for k in range(len(theta_up)):
                r_up = r_up + [
                    N * lambda_0 / (n_e * (1 - e * cos(float(theta_up[k]))))
                    + j * period
                    + period * (1 - self.dc)
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
            r_up = r_up + [N * lambda_0 / (n_e * (1 - e * cos(float(theta_up[k]))))]
        r_down = r_up[::-1]

        xl = []
        yl = []
        for k in range(len(theta_down)):
            xl = xl + [(r_down[k]) * cos(theta_down[k])]
            yl = yl + [(r_down[k]) * sin(theta_down[k])]

        yr = [self.t / 2.0, -self.t / 2.0]

        yl_abs = []
        for k in range(len(yl)):
            yl_abs = yl_abs + [abs(yl[k])]

        y_max = max(yl_abs)
        iy_max = yl_abs.index(y_max)

        L_o = (y_max - self.t / 2) / tan((pi / 180) * self.angle_e / 2)

        xr = [0, 0]

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

        # Reference information
        t = Trans(Trans.R0, 0, -4000)
        text = Text(
            "Ref: 'Universal grating coupler design'\nhttps://doi.org/10.1117/12.2042185\nPCell implementation by: Yun Wang, Timothy Richards, Adam DeAbreu,\nJonas Flueckiger, Charlie Lin, Lukas Chrostowski, Connor Mosquera",
            t,
        )
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        shape.text_halign = 2  # right alignment

        t = Trans(Trans.R0, 0, 4000)
        text = Text(
            "Wavelength: %s\nIncident Angle: %s\nPolarization: %s\nSilicon thickness: %s\nSilicon etch depth: %s"
            % (
                self.wavelength,
                self.theta_c,
                self.pol,
                self.Si_thickness,
                self.etch_depth,
            ),
            t,
        )
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        shape.text_halign = 2  # right alignment
        shape.text_valign = 2  # bottom alignment

        # Device recognition layer
        yr = sin(start) * (
            N * lambda_0 / (n_e * (1 - e * cos(float(start)))) + gc_number * period
        )
        box1 = Box(
            -(self.grating_length + self.taper_length) / dbu - pin_length * 2,
            yr / dbu,
            0,
            -yr / dbu,
        )
        shapes(LayerDevRecN).insert(box1)
