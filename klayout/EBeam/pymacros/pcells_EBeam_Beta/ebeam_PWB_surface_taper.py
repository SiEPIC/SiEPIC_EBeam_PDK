import pya
import math
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_PWB_surface_taper(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the photonic wirebond surface taper
    Author: Becky Lin
    V1: July 30, 2020
    V2: Sept 8, 2020
    V3: Dec 4, 2020
    blin@ece.ubc.ca

    Lukas, 2024/02/12: rounding error on width conversion to integer, fixed using to_itype.
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_PWB_surface_taper, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        self.param("Wtip", self.TypeDouble, "Width of tip (microns)", default=0.13)
        self.param(
            "Wwaveguide", self.TypeDouble, "width of waveguide (microns)", default=0.5
        )
        self.param(
            "edge_offset",
            self.TypeDouble,
            "tip to edge gap (microns, recommend min 30um)",
            default=30,
        )
        self.param(
            "taper_length",
            self.TypeDouble,
            "length of taper (microns, min 45um; max 100um)",
            default=65,
        )
        self.param(
            "OxOp_angle", self.TypeInt, "Oxide open interface angle (int)", default=8
        )
        self.param(
            "show_deepTrench",
            self.TypeBoolean,
            "Show deep trench layer? !Min DT and OxOp is 5um",
            default=True,
        )
        self.param(
            "ZEP_Process",
            self.TypeBoolean,
            "Fabrication using UBC ZEP process",
            default=False,
        )
        self.param(
            "ZEP_Trench", self.TypeDouble, "Trench width for ZEP process", default=10
        )
        self.param(
            "Grouse_Run",
            self.TypeBoolean,
            "Fabrication using ANT Grouse Run",
            default=False,
        )

        # declare the layers
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param(
            "oxopen",
            self.TypeLayer,
            "OxOpen Layer",
            default=TECHNOLOGY["Oxide open (to BOX)"],
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])
        self.param(
            "fibertarget",
            self.TypeLayer,
            "Fiber Target Layer",
            default=TECHNOLOGY["FbrTgt"],
        )
        self.param(
            "ZEP_invert",
            self.TypeLayer,
            "31 Si for ZEP inverse",
            default=LayerInfo(31, 0),
        )
        self.param(
            "Grouse_Si_Keepout",
            self.TypeLayer,
            "Grouse Si Keep-out Layer",
            default=LayerInfo(63, 0),
        )

    def can_create_from_shape_impl(self):
        return False

    def produce(self, layout, layers, parameters, cell):
        # This is the main part of the implementation: create the layout

        #
        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        # import neccessary libraries
        from math import pi, sin, cos, tan
        from SiEPIC._globals import PIN_LENGTH as pin_length
        from SiEPIC.extend import to_itype

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSiN = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerOxOpN = ly.layer(self.oxopen)
        # LayerDTN = ly.layer(self.deeptrench)
        LayerTEXTN = ly.layer(self.textl)
        LayerFbrTgtN = ly.layer(self.fibertarget)
        Layer31SiN = ly.layer(self.ZEP_invert)
        Layer63N = ly.layer(self.Grouse_Si_Keepout)

        w1 = to_itype(self.Wtip, dbu)
        w2 = to_itype(self.Wwaveguide, dbu)
        offset = self.edge_offset
        angle = self.OxOp_angle * (pi / 180)
        excl = 750
        notile = 15
        y_oxop = 20
        l = self.taper_length
        wT = self.ZEP_Trench

        # draw deeptrench layer (to indicate edge)
        pts6 = [
            Point(0, excl / dbu),
            Point(-100 / dbu, excl / dbu),
            Point(-100 / dbu, -excl / dbu),
            Point(0, -excl / dbu),
        ]

        # place deeptrench layer
        OxOp_DT_gap = 0

        if self.show_deepTrench:
            # shapes(LayerDTN).insert(Polygon(pts6))
            OxOp_DT_gap = 5

            # draw no surface element window for edge coupling
            pts5 = [
                Point(0, excl / dbu),
                Point((offset + l + excl) / dbu, excl / dbu),
                Point((offset + l + excl) / dbu, -excl / dbu),
                Point(0, -excl / dbu),
            ]

            t = Trans(Trans.R0, 0, (excl - 800) / dbu)
            text = Text("edge of chip", t)
            shape = shapes(LayerTEXTN).insert(text)
            shape.text_size = 7 / dbu

        else:
            # draw no surface element window for on chip wirebonding
            pts5 = [
                Point(-(excl + l + 150) / dbu, excl / dbu),
                Point((offset + l + excl) / dbu, excl / dbu),
                Point((offset + l + excl) / dbu, -excl / dbu),
                Point(-(excl + l + 150) / dbu, -excl / dbu),
            ]

        # draw the taper
        pts = [
            Point(offset / dbu, w1 / 2),
            Point((l + offset) / dbu, w2 / 2),
            Point((l + offset) / dbu, -w2 / 2),
            Point(offset / dbu, -w1 / 2),
        ]
        # pts = [Point(offset/dbu,-0.001/dbu),Point((offset-20)/dbu,-0.001/dbu),Point((offset-20)/dbu,0.001/dbu),Point(offset/dbu,0.001/dbu),Point(offset/dbu,w1/2),Point((l+offset)/dbu,w2/2),Point((l+offset)/dbu,-w2/2),Point(offset/dbu,-w1/2)]

        # place the taper
        shapes(LayerSiN).insert(Polygon(pts))

        # draw waveguide section
        Lw2 = 15
        pts7 = [
            Point((offset + l) / dbu, (w2 / 2)),
            Point((offset + l + Lw2) / dbu, (w2 / 2)),
            Point((offset + l + Lw2) / dbu, (-w2 / 2)),
            Point((offset + l) / dbu, (-w2 / 2)),
        ]

        # place waveguide section
        shapes(LayerSiN).insert(Polygon(pts7))

        # draw alignment marker
        pts1 = [
            Point((0 + offset) / dbu, 12.4 / dbu),
            Point((0 + offset) / dbu, 9 / dbu),
            Point((3.5 + offset) / dbu, 9 / dbu),
            Point((3.5 + offset) / dbu, 12.5 / dbu),
            Point((0.1 + offset) / dbu, 12.5 / dbu),
            Point((0 + offset) / dbu, 12.6 / dbu),
            Point((0 + offset) / dbu, 16 / dbu),
            Point((-3.5 + offset) / dbu, 16 / dbu),
            Point((-3.5 + offset) / dbu, 12.5 / dbu),
            Point((-0.1 + offset) / dbu, 12.5 / dbu),
        ]

        pts2 = [
            Point((0 + 50 + offset) / dbu, 12.4 / dbu),
            Point((0 + 50 + offset) / dbu, 9 / dbu),
            Point((3.5 + 50 + offset) / dbu, 9 / dbu),
            Point((3.5 + 50 + offset) / dbu, 12.5 / dbu),
            Point((0.1 + 50 + offset) / dbu, 12.5 / dbu),
            Point((0 + 50 + offset) / dbu, 12.6 / dbu),
            Point((0 + 50 + offset) / dbu, 16 / dbu),
            Point((-3.5 + 50 + offset) / dbu, 16 / dbu),
            Point((-3.5 + 50 + offset) / dbu, 12.5 / dbu),
            Point((-0.1 + 50 + offset) / dbu, 12.5 / dbu),
        ]

        # place alignment marker
        shapes(LayerSiN).insert(Polygon(pts1))
        shapes(LayerSiN).insert(Polygon(pts2))

        # draw oxide open window
        dy_oxop = 5
        dx = dy_oxop * tan(angle)
        ddx = sin(angle)
        ddy = cos(angle)
        # pts3 = [Point(OxOp_DT_gap/dbu,y_oxop/dbu),Point((offset+l+10+dx-1)/dbu,dy_oxop/dbu),Point((offset+l+10+dx-ddx)/dbu,(y_oxop-ddy)/dbu),Point((offset+l+10-dx)/dbu,-(y_oxop-10)/dbu),Point(OxOp_DT_gap/dbu,-(y_oxop-10)/dbu)]

        pts3 = [
            Point(OxOp_DT_gap / dbu, y_oxop / dbu),
            Point((offset + l + 10 + dx - 1) / dbu, y_oxop / dbu),
            Point((offset + l + 10 + dx - 1) / dbu, dy_oxop / dbu),
            Point((offset + l + 10 - dx - 1) / dbu, -dy_oxop / dbu),
            Point((offset + l + 10 - dx - 1) / dbu, -(y_oxop - 10) / dbu),
            Point(OxOp_DT_gap / dbu, -(y_oxop - 10) / dbu),
        ]

        # place oxide open window
        shapes(LayerOxOpN).insert(Polygon(pts3))

        # draw devrec box
        pts4 = [
            Point(0, y_oxop / dbu),
            Point((offset + l + 10 + dx) / dbu, y_oxop / dbu),
            Point((offset + l + 10 + dx) / dbu, -(y_oxop - 10) / dbu),
            Point(0, -(y_oxop - 10) / dbu),
        ]

        # place devrec box
        shapes(LayerDevRecN).insert(Polygon(pts5))

        # EXCLUSION LAYERS################################################################

        # place no surface element window
        # shapes(LayerTEXTN).insert(Polygon(pts5))

        # place no surface element text warning
        t = Trans(Trans.R0, 0, (excl - 730) / dbu)
        text = Text(
            "Recommend no surface elements \n(e.g. metals pads, grating couplers, oxide open, etc) \nwithin this DevRec box.\nSurface elements in this box may be covered by cladding photoresist",
            t,
        )
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 7 / dbu

        # ZEP PROCESS#####################################################################

        # draw ZEP process, expanded taper trench used during layer inverting
        # path1 = Path([Point(offset,w2/2),Point((l+offset),w2/2),Point((l+offset),-w2/2),Point(offset,-w2/2)],1)
        # pts8 = [Point(offset/dbu,w2/2),Point((l+offset)/dbu,w2/2),Point((l+offset)/dbu,-w2/2),Point(offset/dbu,-w2/2)]

        # if self.ZEP_Process == True:
        # shapes(Layer31SiN).insert(Polygon(pts8))
        # x = (offset + l)/dbu
        # t = Trans(Trans.R0, x, 0)
        # path1_t = pin.transformed(t)
        # shapes(LayerSiN).insert(path1_t)

        ZEPTrench_pts = [
            Point((offset + 65) / dbu, -wT / dbu),
            Point((offset - 25) / dbu, -wT / dbu),
            Point((offset - 25) / dbu, wT / dbu),
            Point((offset + 65) / dbu, wT / dbu),
        ]
        if self.ZEP_Process == True:
            # place the extended Si Keepout at the tip of taper
            shapes(Layer63N).insert(Polygon(ZEPTrench_pts))

        # GROUSE SI KEEPOUT ##############################################################

        # draw the extended Si Keepout at the tip of taper
        grouseRun_pts = [
            Point(offset / dbu, -2.175 / dbu),
            Point((offset - 25) / dbu, -2.175 / dbu),
            Point((offset - 25) / dbu, 2.175 / dbu),
            Point(offset / dbu, 2.175 / dbu),
        ]
        if self.Grouse_Run == True:
            # place the extended Si Keepout at the tip of taper
            shapes(Layer63N).insert(Polygon(grouseRun_pts))

        #################################################################################

        # draw and place pin on the waveguide:
        x = (offset + l + Lw2) / dbu
        t = Trans(Trans.R0, x, 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w2)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        def circle(x, y, r):
            npts = 180
            theta = 2 * math.pi / npts
            pts = []
            for i in range(0, npts):
                pts.append(
                    Point.from_dpoint(
                        pya.DPoint(
                            (x + r * math.cos(i * theta)) / 1,
                            (y + r * math.sin(i * theta)) / 1,
                        )
                    )
                )
            return pts

        # draw fibre target circle
        align_circle = circle(offset / dbu, 0, 2 / dbu)

        # place fibre target circle
        shapes(LayerFbrTgtN).insert(Polygon(align_circle))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        if self.show_deepTrench:
            return (
                "PWB_taper (tip_width="
                + ("%.2f" % self.Wtip)
                + ",waveguide_width="
                + ("%.2f" % self.Wwaveguide)
                + ",taper_length="
                + ("%.1f" % self.taper_length)
                + ",Angle="
                + ("%s" % self.OxOp_angle)
                + ",edge_offset="
                + ("%.2f" % self.edge_offset)
                + ")"
            )
        else:
            return (
                "PWB_taper (tip_width="
                + ("%.2f" % self.Wtip)
                + ",waveguide_width="
                + ("%.2f" % self.Wwaveguide)
                + ",taper_length="
                + ("%.1f" % self.taper_length)
                + ",Angle="
                + ("%s" % self.OxOp_angle)
                + ")"
            )
