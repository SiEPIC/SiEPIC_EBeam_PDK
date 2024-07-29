import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_irph_wg(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the IRPH straight waveguide.

    Authors: Jaspreet Jhoja, Lukas Chrostowski
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_irph_wg, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("w_rib", self.TypeDouble, "Waveguide Rib Width", default=24)
        self.param("length", self.TypeDouble, "Waveguide length", default=100)
        self.param("n_w", self.TypeDouble, "N Width", default=22)
        self.param("npp_w", self.TypeDouble, "N++ Width (um)", default=10)
        self.param("npp_dw", self.TypeDouble, "N++ Edge to Si Edge (um)", default=2)
        self.param("vc_dw", self.TypeDouble, "VC Edge to Si Edge (um)", default=5)
        self.param("vc_w", self.TypeDouble, "VC Width", default=5)
        self.param("m_dw", self.TypeDouble, "Metal edge to Si Edge (um)", default=4)
        self.param("m_w", self.TypeDouble, "Metal Width", default=10)
        self.param(
            "overlay",
            self.TypeDouble,
            "Overlay accuracy (optical litho) (um)",
            default=1,
        )
        self.param(
            "overlay_ebl", self.TypeDouble, "Overlay accuracy (EBL) (um)", default=0.05
        )
        self.param(
            "io_wg_type",
            self.TypeBoolean,
            "I/O waveguide type, 0 - strip; 1 - rib",
            default=0,
        )

        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "siriblayer",
            self.TypeLayer,
            "Si rib Layer",
            default=TECHNOLOGY["Si - 90 nm rib"],
        )
        self.param("nlayer", self.TypeLayer, "N Layer", default=TECHNOLOGY["Si N"])
        self.param(
            "npplayer", self.TypeLayer, "N++ Layer", default=TECHNOLOGY["Si N++"]
        )
        self.param("vclayer", self.TypeLayer, "VC Layer", default=TECHNOLOGY["VC"])
        self.param(
            "mlayer", self.TypeLayer, "Metal Layer", default=TECHNOLOGY["M2_router"]
        )
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ebeam_irph_wg"  # (R=" + ('%.3f' % self.r) + ",g=" + ('%g' % (1000*self.g)) + ")"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        from SiEPIC._globals import PIN_LENGTH
        from SiEPIC.extend import to_itype

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSiN = ly.layer(self.silayer)
        LayerSiRibN = ly.layer(self.siriblayer)
        LayerNN = ly.layer(self.nlayer)
        LayerNPPN = ly.layer(self.npplayer)
        LayerVCN = ly.layer(self.vclayer)
        LayerMN = ly.layer(self.mlayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)

        w = to_itype(self.w, dbu)
        w_rib = to_itype(self.w_rib, dbu)
        length = to_itype(self.length, dbu)
        n_w = to_itype(self.n_w, dbu)
        npp_w = to_itype(self.npp_w, dbu)
        npp_dw = to_itype(self.npp_dw, dbu)
        vc_w = to_itype(self.vc_w, dbu)
        vc_dw = to_itype(self.vc_dw, dbu)
        m_dw = to_itype(self.m_dw, dbu)
        m_w = to_itype(self.m_w, dbu)
        overlay = to_itype(self.overlay, dbu)
        overlay_ebl = to_itype(self.overlay_ebl, dbu)

        if self.io_wg_type == 0:
            ## define strip to slab transfer taper parameters
            N = 100  # Number of points for the input/output slab taper
            order = 3  # input/output slab taper curve
            in_taper = to_itype(5, dbu)  # length of taper
            taper_w = to_itype(2, dbu)
            # add input slab taper
            pts = []
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        -in_taper + in_taper / N * i,
                        (w - overlay_ebl * 2) / 2
                        + ((taper_w - (w - overlay_ebl * 2)) / (N**order)) * (i**order),
                    )
                )
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        -in_taper + in_taper / N * (N - i),
                        -(w - overlay_ebl * 2) / 2
                        - ((taper_w - (w - overlay_ebl * 2)) / (N**order))
                        * ((N - i) ** order),
                    )
                )
            self.cell.shapes(LayerSiRibN).insert(Polygon(pts))
            # add output slab taper
            pts = []
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        length + in_taper - in_taper / N * i,
                        (w - overlay_ebl * 2) / 2
                        + ((taper_w - (w - overlay_ebl * 2)) / (N**order)) * (i**order),
                    )
                )
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        length + in_taper - in_taper / N * (N - i),
                        -(w - overlay_ebl * 2) / 2
                        - ((taper_w - (w - overlay_ebl * 2)) / (N**order))
                        * ((N - i) ** order),
                    )
                )
            self.cell.shapes(LayerSiRibN).insert(Polygon(pts))
        else:
            in_taper = 0  # length of taper
            taper_w = 0  # width of taper

        # draw the waveguide
        xtop = 0 - in_taper
        ytop = -1 * (w / 2)
        xbottom = length + in_taper
        ybottom = 1 * (w / 2)
        wg1 = Box(xtop, -w / 2, xbottom, w / 2)
        shapes(LayerSiN).insert(wg1)

        # Pins on the bottom waveguide side:
        pin = Path(
            [Point(xtop + PIN_LENGTH / 2, 0), Point(xtop - PIN_LENGTH / 2, 0)], w
        )
        shapes(LayerPinRecN).insert(pin)
        text = Text("pin1", Trans(Trans.R0, xtop, 0))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        pin = Path(
            [Point(xbottom - PIN_LENGTH / 2, 0), Point(xbottom + PIN_LENGTH / 2, 0)], w
        )
        shapes(LayerPinRecN).insert(pin)
        text = Text("pin2", Trans(Trans.R0, xbottom, 0))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # draw N
        b = Box(0, -n_w / 2, length, n_w / 2)
        shapes(LayerNN).insert(b)

        # draw NPP
        b = Box(0, npp_dw + w / 2, length, npp_dw + w / 2 + npp_w)
        shapes(LayerNPPN).insert(b)
        b = Box(0, -npp_dw - w / 2, length, -npp_dw - w / 2 - npp_w)
        shapes(LayerNPPN).insert(b)

        # draw via
        b = Box(overlay, vc_dw + w / 2, length - overlay, vc_dw + w / 2 + vc_w)
        shapes(LayerVCN).insert(b)
        b = Box(overlay, -vc_dw - w / 2, length - overlay, -vc_dw - w / 2 - vc_w)
        shapes(LayerVCN).insert(b)

        # draw metal
        b = Box(0, m_dw + w / 2, length, m_dw + w / 2 + m_w)
        shapes(LayerMN).insert(b)
        b = Box(0, -m_dw - w / 2, length, -m_dw - w / 2 - m_w)
        shapes(LayerMN).insert(b)

        # devrec layer
        w_devrec = 2 * max(
            m_dw + m_w + w / 2, vc_dw + w / 2 + vc_w, npp_dw + w / 2 + npp_w, w_rib / 2
        )
        pts = []
        pts = [
            Point(0, -w_devrec / 2 - w),
            Point(0, -taper_w),
            Point(0 - in_taper, -taper_w),
            Point(0 - in_taper, +taper_w),
            Point(0, +taper_w),
            Point(0, w_devrec / 2 + w),
            Point(length, w_devrec / 2 + w),
            Point(length, +taper_w),
            Point(length + in_taper, +taper_w),
            Point(length + in_taper, -taper_w),
            Point(length, -taper_w),
            Point(length, -w_devrec / 2 - w),
        ]
        self.cell.shapes(LayerDevRecN).insert(Polygon(pts))

        # Si rib layer
        b = Box(0, w_rib / 2, length, -w_rib / 2)
        shapes(LayerSiRibN).insert(b)

        t = Trans(Trans.R0, 0, 0)
        text = Text("Component=ebeam_irph_wg", t)
        shape = shapes(LayerDevRecN).insert(text)
        # shape.text_size = self.r*0.07/dbu


#    print("Done drawing the layout for - ebeam_irph_wg: %.3f-%g" % ( self.r, self.g))
