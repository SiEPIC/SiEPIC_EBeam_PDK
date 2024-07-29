import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_rib_phase_shifter_folded_inside(pya.PCellDeclarationHelper):
    # N-doped heater phase shifter in a rib waveguide
    # design by Guowu Zhang <guowu.zhang@mail.mcgill.ca>
    # and Lukas Chrostowski
    # based on Ref: R. Priti, "Efficiency Improvement of an O-band SOI-MZI Thermo-optic Matrix Switch"
    # and folding based on
    # Ref: Z. Lu, "Michelson Interferometer Thermo-optic Switch on SOI with a 50 uW Power Consumption", IEEE PTL, 2015

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_rib_phase_shifter_folded_inside, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "io_wg_type",
            self.TypeBoolean,
            "I/O waveguide type, 0 - strip; 1 - rib",
            default=0,
        )
        self.param(
            "include_oxide_open",
            self.TypeBoolean,
            "Include thermal isolation etch, 0 - no; 1 - yes",
            default=0,
        )
        self.param(
            "fold_number", self.TypeInt, "Number of folds (3, 5, 7, ...)", default=5
        )
        self.param(
            "input_rib_width", self.TypeDouble, "Input Rib Width (um)", default=0.35
        )
        self.param(
            "input_slab_width", self.TypeDouble, "Input Slab Width (um)", default=2
        )
        self.param(
            "in_taper_length", self.TypeDouble, "Input Taper Length (um)", default=15
        )
        self.param("length", self.TypeDouble, "Phase Shifter Length (um)", default=150)
        self.param("width", self.TypeDouble, "Waveguide Width (um)", default=0.5)
        self.param("gap", self.TypeDouble, "Waveguide gap (um)", default=2)

        #    self.param("ps_slab_width", self.TypeDouble, "Phase Shifter Slab Width (um)", default = 18)
        self.param("npp_width", self.TypeDouble, "Npp Width (um)", default=2)
        self.param(
            "npp_distance", self.TypeDouble, "Npp Edge to Si Edge (um)", default=2
        )
        self.param("segments", self.TypeInt, "Phase Shifter Segments", default=5)
        self.param(
            "overlay",
            self.TypeDouble,
            "Overlay accuracy (optical litho) (um)",
            default=1,
        )
        self.param(
            "overlay_ebl", self.TypeDouble, "Overlay accuracy (EBL) (um)", default=0.05
        )
        #    self.param("vc_dw", self.TypeDouble, "VC Offset", default = 5)
        self.param("vc_w", self.TypeDouble, "Contact via width", default=5)
        #    self.param("m_dw", self.TypeDouble, "Metal Offset", default = 4)
        self.param("m_w", self.TypeDouble, "Metal Width", default=10)
        self.param(
            "slayer", self.TypeLayer, "Slab Layer", default=TECHNOLOGY["Si - 90 nm rib"]
        )
        #    self.param("nlayer", self.TypeLayer, "N Layer", default = TECHNOLOGY['Si N'])
        self.param(
            "npplayer", self.TypeLayer, "N++ Layer", default=TECHNOLOGY["Si N++"]
        )
        self.param("vclayer", self.TypeLayer, "VC Layer", default=TECHNOLOGY["VC"])
        self.param(
            "mlayer", self.TypeLayer, "Metal Layer", default=TECHNOLOGY["M2_router"]
        )
        self.param(
            "oolayer",
            self.TypeLayer,
            "Thermal Isolation Layer",
            default=TECHNOLOGY["Oxide open (to BOX)"],
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
        return "ebeam_rib_phase_shifter_folded_inside(L=" + ("%.3f" % self.length) + ")"

    def produce(self, layout, layers, parameters, cell):
        # coerce parameters (make consistent)

        self._layers = layers
        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        # cell: layout cell to place the layout
        # LayerSiN: which layer to use
        # r: radius
        # w: waveguide width
        # length units in dbu

        from SiEPIC._globals import PIN_LENGTH
        from SiEPIC.utils.layout import layout_waveguide2
        from SiEPIC.extend import to_itype

        # fetch the parameters
        TECHNOLOGY = get_technology_by_name("EBeam")
        dbu = self.layout.dbu
        ly = self.layout

        LayerSiN = ly.layer(self.silayer)
        LayerSlab = ly.layer(self.slayer)
        #    LayerNN = ly.layer(self.nlayer)
        LayerNPPN = ly.layer(self.npplayer)
        LayerVCN = ly.layer(self.vclayer)
        LayerMN = ly.layer(self.mlayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)
        Layeroxideopen = ly.layer(self.oolayer)

        ## define parameters for phase shifter
        overlay = to_itype(self.overlay, dbu)
        overlay_ebl = to_itype(self.overlay_ebl, dbu)

        ## define waveguide related parameters
        radius_um, adiab, bezier = 5, 1, 0.2
        w = to_itype(self.width, dbu)  # waveguide width, default 0.5 um
        l = to_itype(self.length, dbu)  # pahse shifter length, default 150 um
        npp_d = to_itype(self.npp_distance, dbu)  # npp to center waveguide distance
        sw = (npp_d + w / 2) * 2  # twice of npp_d that is defined above
        in_rib = to_itype(
            self.input_rib_width, dbu
        )  # the slab width of the input/output waveguide to the phase shifter
        in_taper = to_itype(
            self.in_taper_length, dbu
        )  # the input waveguide to phase shifter dimension transfer taper length, default 15
        edge_slab_width = to_itype(
            4, dbu
        )  # width of the 90 nm slab that is outside of all the folding waveguide, default 2 * 2um
        npp_width = to_itype(self.npp_width, dbu)  # npp width, default 5 um

        ## define waveguide folding parameters
        folding_n = int(
            round((self.fold_number - 1) / 2)
        )  # folding waveguide number on one side
        folding_w1 = w + 50  # one of the folding waveguide width
        folding_w2 = w - 50  # the other one of the folding waveguide width
        folding_gap = to_itype(self.gap, dbu)  # the gap between two folding waveguide
        routing_step = to_itype(
            radius_um, dbu
        )  # define how large the U shape should be, default 20

        ## define node related parameters
        contact_size = to_itype(self.vc_w, dbu)  # square NPP size, for VC purpose
        pin_text_size = to_itype(0.4, dbu)  # pin text size

        metal_routing_distance_to_node = to_itype(
            20, dbu
        )  # *** calculate from PCell parameters ***
        metal_routing_width = to_itype(self.m_w, dbu)  # width of metal
        vc_to_npp_exclusion = to_itype(
            self.overlay, dbu
        )  # VC boundary to NPP boundary distance

        ps_sl_w = (
            sw + 2 * contact_size + folding_n * 2 * (w + folding_gap + overlay_ebl)
        )  # overall pahse shifter 90nm slab width

        oxide_open_to_silicon_gap = 3 / dbu
        oxide_open_width = 3 / dbu

        # measure the total length of the waveguides
        total_waveguide_length = 0

        ## define strip to slab transfer taper parameters
        N = 100  # Number of points for the input/output slab taper
        order = 3  # input/output slab taper curve

        pts = [Point(-l / 2, 0), Point(l / 2, 0)]
        total_waveguide_length += layout_waveguide2(
            TECHNOLOGY,
            self.layout,
            self.cell,
            ["Si"],
            [folding_w2 * dbu],
            [0],
            pts,
            radius_um,
            adiab,
            bezier,
        )

        if self.io_wg_type:
            in_slab = to_itype(self.input_slab_width, dbu)
        else:
            in_slab = in_rib

        if folding_n > 0:
            ps_sl_w = (
                contact_size * 2
                + sw * 2
                + (folding_w1 + folding_w2 + folding_gap * 2) * folding_n
                + edge_slab_width
            )

            pts = [
                Point(-l / 2 - in_taper, -w / 2),
                Point(-l / 2, -folding_w2 / 2),
                Point(-l / 2, folding_w2 / 2),
                Point(-l / 2 - in_taper, w / 2),
            ]  # fix waveguide width mismatch for left center input taper
            self.cell.shapes(LayerSiN).insert(Polygon(pts))

            # add input slab taper
            pts = []
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        -l / 2 - in_taper + in_taper / N * i,
                        (w - overlay_ebl) / 2
                        + ((2 / dbu - (w - overlay_ebl)) / (N**order)) * (i**order),
                    )
                )
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        -l / 2 - in_taper + in_taper / N * (N - i),
                        -(w - overlay_ebl) / 2
                        - ((2 / dbu - (w - overlay_ebl)) / (N**order))
                        * ((N - i) ** order),
                    )
                )
            self.cell.shapes(LayerSlab).insert(Polygon(pts))

            # add output strip taper
            pts = [
                Point(l / 2 + in_taper, -w / 2),
                Point(l / 2, -folding_w2 / 2),
                Point(l / 2, folding_w2 / 2),
                Point(l / 2 + in_taper, w / 2),
            ]
            # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
            self.cell.shapes(LayerSiN).insert(Polygon(pts))
            total_waveguide_length += in_taper * dbu

            # add input slab taper
            pts = []
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        l / 2 + in_taper - in_taper / N * i,
                        (w - overlay_ebl) / 2
                        + ((2 / dbu - (w - overlay_ebl)) / (N**order)) * (i**order),
                    )
                )
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        l / 2 + in_taper / N * i,
                        -(w - overlay_ebl) / 2
                        - ((2 / dbu - (w - overlay_ebl)) / (N**order))
                        * ((N - i) ** order),
                    )
                )
            self.cell.shapes(LayerSlab).insert(Polygon(pts))

            for i in range(0, folding_n):
                y_coordinate = (
                    folding_gap + w
                )  # move up/down the position according to vc_to_npp_exclusion
                y_move = (
                    i * (folding_w1 + folding_w2 + folding_gap * 2) / 2 + y_coordinate
                )
                if i % 2:
                    folding_w = folding_w2
                else:
                    folding_w = folding_w1

                # waveguide in the heated region
                pts = [Point(-l / 2, y_move), Point(l / 2, y_move)]
                total_waveguide_length += layout_waveguide2(
                    TECHNOLOGY,
                    self.layout,
                    self.cell,
                    ["Si"],
                    [folding_w * dbu],
                    [0],
                    pts,
                    radius_um,
                    adiab,
                    bezier,
                )
                pts = [Point(-l / 2, -y_move), Point(l / 2, -y_move)]
                total_waveguide_length += layout_waveguide2(
                    TECHNOLOGY,
                    self.layout,
                    self.cell,
                    ["Si"],
                    [folding_w * dbu],
                    [0],
                    pts,
                    radius_um,
                    adiab,
                    bezier,
                )

                # add upper left input taper
                pts = [
                    Point(-l / 2 - in_taper, -w / 2 + y_move),
                    Point(-l / 2, -folding_w / 2 + y_move),
                    Point(-l / 2, folding_w / 2 + y_move),
                    Point(-l / 2 - in_taper, w / 2 + y_move),
                ]
                # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
                self.cell.shapes(LayerSiN).insert(Polygon(pts))
                total_waveguide_length += in_taper * dbu

                # slab cubic taper
                pts = []
                for ii in range(0, N + 1):
                    pts.append(
                        Point(
                            -l / 2 - in_taper + in_taper / N * ii,
                            (w - overlay_ebl) / 2
                            + ((2 / dbu - (w - overlay_ebl)) / (N**order)) * (ii**order)
                            + y_move,
                        )
                    )
                for ii in range(0, N + 1):
                    pts.append(
                        Point(
                            -l / 2 - in_taper + in_taper / N * (N - ii),
                            -(w - overlay_ebl) / 2
                            - ((2 / dbu - (w - overlay_ebl)) / (N**order))
                            * ((N - ii) ** order)
                            + y_move,
                        )
                    )
                self.cell.shapes(LayerSlab).insert(Polygon(pts))

                if i != folding_n - 1:
                    # add below left taper
                    y_move = -y_move
                    pts = [
                        Point(-l / 2 - in_taper, -w / 2 + y_move),
                        Point(-l / 2, -folding_w / 2 + y_move),
                        Point(-l / 2, folding_w / 2 + y_move),
                        Point(-l / 2 - in_taper, w / 2 + y_move),
                    ]
                    # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
                    self.cell.shapes(LayerSiN).insert(Polygon(pts))
                    total_waveguide_length += in_taper * dbu

                    # slab cubic taper
                    pts = []
                    for ii in range(0, N + 1):
                        pts.append(
                            Point(
                                -l / 2 - in_taper + in_taper / N * ii,
                                (w - overlay_ebl) / 2
                                + ((2 / dbu - (w - overlay_ebl)) / (N**order))
                                * (ii**order)
                                + y_move,
                            )
                        )
                    for ii in range(0, N + 1):
                        pts.append(
                            Point(
                                -l / 2 - in_taper + in_taper / N * (N - ii),
                                -(w - overlay_ebl) / 2
                                - ((2 / dbu - (w - overlay_ebl)) / (N**order))
                                * ((N - ii) ** order)
                                + y_move,
                            )
                        )
                    self.cell.shapes(LayerSlab).insert(Polygon(pts))

                    # add upper right taper
                    y_move = -y_move
                    pts = [
                        Point(l / 2 + in_taper, -w / 2 + y_move),
                        Point(l / 2, -folding_w / 2 + y_move),
                        Point(l / 2, folding_w / 2 + y_move),
                        Point(l / 2 + in_taper, w / 2 + y_move),
                    ]
                    # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
                    self.cell.shapes(LayerSiN).insert(Polygon(pts))
                    total_waveguide_length += in_taper * dbu

                    # slab cubic taper
                    pts = []
                    for ii in range(0, N + 1):
                        pts.append(
                            Point(
                                l / 2 + in_taper - in_taper / N * ii,
                                (w - overlay_ebl) / 2
                                + ((2 / dbu - (w - overlay_ebl)) / (N**order))
                                * (ii**order)
                                + y_move,
                            )
                        )
                    for ii in range(0, N + 1):
                        pts.append(
                            Point(
                                l / 2 + in_taper / N * ii,
                                -(w - overlay_ebl) / 2
                                - ((2 / dbu - (w - overlay_ebl)) / (N**order))
                                * ((N - ii) ** order)
                                + y_move,
                            )
                        )
                    self.cell.shapes(LayerSlab).insert(Polygon(pts))

                else:
                    y_move = -y_move
                    # add input strip taper
                    pts = [
                        Point(-l / 2 - in_taper, -w / 2 + y_move),
                        Point(-l / 2, -folding_w / 2 + y_move),
                        Point(-l / 2, folding_w / 2 + y_move),
                        Point(-l / 2 - in_taper, w / 2 + y_move),
                    ]
                    # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
                    self.cell.shapes(LayerSiN).insert(Polygon(pts))
                    total_waveguide_length += in_taper * dbu

                    # add input slab taper
                    pts = []
                    for i in range(0, N + 1):
                        pts.append(
                            Point(
                                -l / 2 - in_taper + in_taper / N * i,
                                in_slab / 2
                                + ((2 / dbu - (w - overlay_ebl)) / (N**order))
                                * (i**order)
                                + y_move,
                            )
                        )
                    for i in range(0, N + 1):
                        pts.append(
                            Point(
                                -l / 2 - in_taper + in_taper / N * (N - i),
                                -in_slab / 2
                                - ((2 / dbu - (w - overlay_ebl)) / (N**order))
                                * ((N - i) ** order)
                                + y_move,
                            )
                        )
                    self.cell.shapes(LayerSlab).insert(Polygon(pts))

                    # add output strip taper
                    y_move = -y_move
                    pts = [
                        Point(l / 2 + in_taper, -w / 2 + y_move),
                        Point(l / 2, -folding_w / 2 + y_move),
                        Point(l / 2, folding_w / 2 + y_move),
                        Point(l / 2 + in_taper, w / 2 + y_move),
                    ]
                    # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
                    self.cell.shapes(LayerSiN).insert(Polygon(pts))
                    total_waveguide_length += in_taper * dbu

                    # add input slab taper
                    pts = []
                    for i in range(0, N + 1):
                        pts.append(
                            Point(
                                l / 2 + in_taper - in_taper / N * i,
                                in_slab / 2
                                + ((2 / dbu - (w - overlay_ebl)) / (N**order))
                                * (i**order)
                                + y_move,
                            )
                        )
                    for i in range(0, N + 1):
                        pts.append(
                            Point(
                                l / 2 + in_taper / N * i,
                                -in_slab / 2
                                - ((2 / dbu - (w - overlay_ebl)) / (N**order))
                                * ((N - i) ** order)
                                + y_move,
                            )
                        )
                    self.cell.shapes(LayerSlab).insert(Polygon(pts))

                    # Pin on the left side:
                    wg_start = -(l / 2 + in_taper + routing_step * folding_n * 3 + w)
                    p1 = [
                        Point(wg_start + PIN_LENGTH / 2, -y_move),
                        Point(wg_start - PIN_LENGTH / 2, -y_move),
                    ]
                    p1c = Point(wg_start, -y_move)
                    self.set_p1 = p1c
                    self.p1 = p1c
                    pin = Path(p1, w)
                    self.cell.shapes(LayerPinRecN).insert(pin)
                    t = Trans(Trans.R0, wg_start, -y_move)
                    text = Text("pin1", t)
                    shape = self.cell.shapes(LayerPinRecN).insert(text)
                    shape.text_size = pin_text_size
                    # Waveguide to route to port, new in SiEPIC-Tools v0.3.64
                    pts = [Point(-l / 2 - in_taper, -y_move), Point(wg_start, -y_move)]
                    if self.io_wg_type:
                        waveguide_length = layout_waveguide2(
                            TECHNOLOGY,
                            self.layout,
                            self.cell,
                            ["Si", "Si - 90 nm rib"],
                            [w * dbu, in_slab * dbu],
                            [0, 0],
                            pts,
                            radius_um,
                            adiab,
                            bezier,
                        )
                    else:
                        waveguide_length = layout_waveguide2(
                            TECHNOLOGY,
                            self.layout,
                            self.cell,
                            ["Si"],
                            [w * dbu],
                            [0],
                            pts,
                            radius_um,
                            adiab,
                            bezier,
                        )

                    # Pin & Waveguide on the right side:
                    wg_end = l / 2 + in_taper + routing_step * folding_n * 3 + w
                    p2 = [
                        Point(wg_end - PIN_LENGTH / 2, y_move),
                        Point(wg_end + PIN_LENGTH / 2, y_move),
                    ]
                    p2c = Point(wg_end, y_move)
                    self.set_p2 = p2c
                    self.p2 = p2c
                    pin = Path(p2, w)
                    self.cell.shapes(LayerPinRecN).insert(pin)
                    t = Trans(Trans.R0, wg_end, y_move)
                    text = Text("pin2", t)
                    shape = self.cell.shapes(LayerPinRecN).insert(text)
                    shape.text_size = pin_text_size
                    # Waveguide to route to port, new in SiEPIC-Tools v0.3.64
                    pts = [Point(l / 2 + in_taper, y_move), Point(wg_end, y_move)]
                    if self.io_wg_type:
                        total_waveguide_length += layout_waveguide2(
                            TECHNOLOGY,
                            self.layout,
                            self.cell,
                            ["Si", "Si - 90 nm rib"],
                            [w * dbu, in_slab * dbu],
                            [0, 0],
                            pts,
                            radius_um,
                            adiab,
                            bezier,
                        )
                    else:
                        total_waveguide_length += layout_waveguide2(
                            TECHNOLOGY,
                            self.layout,
                            self.cell,
                            ["Si"],
                            [w * dbu],
                            [0],
                            pts,
                            radius_um,
                            adiab,
                            bezier,
                        )

                # add below right taper
                y_move = -y_move
                pts = [
                    Point(l / 2 + in_taper, -w / 2 + y_move),
                    Point(l / 2, -folding_w / 2 + y_move),
                    Point(l / 2, folding_w / 2 + y_move),
                    Point(l / 2 + in_taper, w / 2 + y_move),
                ]
                # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
                self.cell.shapes(LayerSiN).insert(Polygon(pts))
                total_waveguide_length += in_taper * dbu
                pts = []
                for ii in range(0, N + 1):
                    pts.append(
                        Point(
                            l / 2 + in_taper - in_taper / N * ii,
                            (w - overlay_ebl) / 2
                            + ((2 / dbu - (w - overlay_ebl)) / (N**order)) * (ii**order)
                            + y_move,
                        )
                    )
                for ii in range(0, N + 1):
                    pts.append(
                        Point(
                            l / 2 + in_taper / N * ii,
                            -(w - overlay_ebl) / 2
                            - ((2 / dbu - (w - overlay_ebl)) / (N**order))
                            * ((N - ii) ** order)
                            + y_move,
                        )
                    )
                self.cell.shapes(LayerSlab).insert(Polygon(pts))

            # add metal contact and folded waveguides
            for i in range(-folding_n, folding_n):
                y_coordinate = (
                    folding_gap + w
                )  # move up/down the position according to vc_to_npp_exclusion
                if i < 0:
                    y_origin = (i + 1) * (
                        folding_w1 + folding_w2 + folding_gap * 2
                    ) / 2 - y_coordinate
                if i == 0:
                    y_origin = 0
                if i > 0:
                    y_origin = (i - 1) * (
                        folding_w1 + folding_w2 + folding_gap * 2
                    ) / 2 + y_coordinate

                if (i + 1) < 0:
                    y_end = (i + 2) * (
                        folding_w1 + folding_w2 + folding_gap * 2
                    ) / 2 - y_coordinate
                if (i + 1) == 0:
                    y_end = 0
                if (i + 1) > 0:
                    y_end = (
                        i * (folding_w1 + folding_w2 + folding_gap * 2) / 2
                        + y_coordinate
                    )

                # Calculate the Folded waveguide vertices
                if (i + folding_n) % 2:
                    # Waveguides on the left side
                    if y_origin + routing_step * 2 - y_end < 2 * radius_um:
                        y_routing = max(routing_step * 2, y_end - y_origin)
                    else:
                        y_routing = y_end + routing_step * 2
                    path = Path(
                        [
                            Point(-l / 2 - in_taper, y_origin),
                            Point(
                                -l / 2
                                - in_taper
                                - routing_step * (1.5 * folding_n - 1.5 * i + 1.5),
                                y_origin,
                            ),
                            Point(
                                -l / 2
                                - in_taper
                                - routing_step * (1.5 * folding_n - 1.5 * i + 1.5),
                                y_routing,
                            ),
                            Point(
                                -l / 2
                                - in_taper
                                - routing_step * (1.5 * folding_n - 1.5 * i - 0.5),
                                y_routing,
                            ),
                            Point(
                                -l / 2
                                - in_taper
                                - routing_step * (1.5 * folding_n - 1.5 * i - 0.5),
                                y_end,
                            ),
                            Point(-l / 2 - in_taper, y_end),
                        ],
                        0,
                    )

                else:
                    # Waveguides on the right side
                    if y_origin - y_end + routing_step * 2 < 2 * radius_um:
                        y_routing = -max(routing_step * 2, y_end - y_origin)
                    else:
                        y_routing = y_origin - routing_step * 2
                    path = Path(
                        [
                            Point(l / 2 + in_taper, y_origin),
                            Point(
                                l / 2
                                + in_taper
                                + routing_step * (1.5 * folding_n + 1.5 * i + 1),
                                y_origin,
                            ),
                            Point(
                                l / 2
                                + in_taper
                                + routing_step * (1.5 * folding_n + 1.5 * i + 1),
                                y_routing,
                            ),
                            Point(
                                l / 2
                                + in_taper
                                + routing_step * (1.5 * folding_n + 1.5 * i + 3),
                                y_routing,
                            ),
                            Point(
                                l / 2
                                + in_taper
                                + routing_step * (1.5 * folding_n + 1.5 * i + 3),
                                y_end,
                            ),
                            Point(l / 2 + in_taper, y_end),
                        ],
                        0,
                    )

                # Draw the waveguide geometry, new in SiEPIC-Tools v0.3.64
                path.unique_points()
                pts = path.get_points()
                total_waveguide_length += layout_waveguide2(
                    TECHNOLOGY,
                    self.layout,
                    self.cell,
                    ["Si"],
                    [w * dbu],
                    [0],
                    pts,
                    radius_um,
                    adiab,
                    bezier,
                )

        for i in range(0, self.segments + 1):
            y_increase = -y_move

            wg_temp_upper = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 - vc_to_npp_exclusion,
                sw / 2 + y_increase,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                + vc_to_npp_exclusion,
                sw / 2 + contact_size + 2 * vc_to_npp_exclusion + y_increase,
            )
            # self.cell.shapes(LayerNN).insert(wg_temp_upper)
            self.cell.shapes(LayerNPPN).insert(wg_temp_upper)

            wg_temp_upper = pya.Box(
                (l - contact_size) / self.segments * i
                - l / 2
                - 2 * vc_to_npp_exclusion,
                sw / 2 + y_increase,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                + 2 * vc_to_npp_exclusion,
                sw / 2 + contact_size + 3 * vc_to_npp_exclusion + y_increase,
            )
            self.cell.shapes(LayerSlab).insert(wg_temp_upper)

            #        self.cell.shapes(LayerNN).insert(wg_temp_upper)
            vc_temp_upper = pya.Box(
                (l - contact_size) / self.segments * i - l / 2,
                sw / 2 + vc_to_npp_exclusion + y_increase,
                (l - contact_size) / self.segments * i - l / 2 + contact_size,
                sw / 2 + contact_size + vc_to_npp_exclusion + y_increase,
            )
            self.cell.shapes(LayerVCN).insert(vc_temp_upper)

            wg_temp_lower = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 - vc_to_npp_exclusion,
                -sw / 2 - y_increase,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                + vc_to_npp_exclusion,
                -sw / 2 - contact_size - 2 * vc_to_npp_exclusion - y_increase,
            )
            # self.cell.shapes(LayerNN).insert(wg_temp_lower)
            self.cell.shapes(LayerNPPN).insert(wg_temp_lower)
            #        self.cell.shapes(LayerNN).insert(wg_temp_lower)

            wg_temp_lower = pya.Box(
                (l - contact_size) / self.segments * i
                - l / 2
                - 2 * vc_to_npp_exclusion,
                -sw / 2 - y_increase,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                + 2 * vc_to_npp_exclusion,
                -sw / 2 - contact_size - 3 * vc_to_npp_exclusion - y_increase,
            )
            self.cell.shapes(LayerSlab).insert(wg_temp_lower)

            vc_temp_lower = pya.Box(
                (l - contact_size) / self.segments * i - l / 2,
                -sw / 2 - vc_to_npp_exclusion - y_increase,
                (l - contact_size) / self.segments * i - l / 2 + contact_size,
                -sw / 2 - contact_size - vc_to_npp_exclusion - y_increase,
            )
            self.cell.shapes(LayerVCN).insert(vc_temp_lower)

            metal_temp = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 - vc_to_npp_exclusion,
                -sw / 2
                - contact_size
                - metal_routing_distance_to_node * (i % 2)
                - 2 * vc_to_npp_exclusion
                - y_increase,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                + vc_to_npp_exclusion,
                sw / 2
                + contact_size
                + metal_routing_distance_to_node * ((i + 1) % 2)
                + 2 * vc_to_npp_exclusion
                + y_increase,
            )
            self.cell.shapes(LayerMN).insert(metal_temp)

            if self.include_oxide_open & (i < self.segments):
                oxide_open_temp = pya.Box(
                    (l - contact_size) / self.segments * i
                    - l / 2
                    + contact_size
                    + 2 * vc_to_npp_exclusion
                    + oxide_open_to_silicon_gap,
                    npp_d
                    + w / 2
                    + npp_width
                    + y_increase
                    + edge_slab_width / 2
                    + oxide_open_to_silicon_gap,
                    (l - contact_size) / self.segments * (i + 1)
                    - l / 2
                    - oxide_open_to_silicon_gap
                    - 2 * vc_to_npp_exclusion,
                    npp_d
                    + w / 2
                    + npp_width
                    + y_increase
                    + edge_slab_width / 2
                    + oxide_open_to_silicon_gap
                    + oxide_open_width,
                )

                self.cell.shapes(Layeroxideopen).insert(oxide_open_temp)

                oxide_open_temp = pya.Box(
                    (l - contact_size) / self.segments * i
                    - l / 2
                    + contact_size
                    + 2 * vc_to_npp_exclusion
                    + oxide_open_to_silicon_gap,
                    -(
                        npp_d
                        + w / 2
                        + npp_width
                        + y_increase
                        + edge_slab_width / 2
                        + oxide_open_to_silicon_gap
                    ),
                    (l - contact_size) / self.segments * (i + 1)
                    - l / 2
                    - oxide_open_to_silicon_gap
                    - 2 * vc_to_npp_exclusion,
                    -(
                        npp_d
                        + w / 2
                        + npp_width
                        + y_increase
                        + edge_slab_width / 2
                        + oxide_open_to_silicon_gap
                        + oxide_open_width
                    ),
                )

                self.cell.shapes(Layeroxideopen).insert(oxide_open_temp)

        wg2 = pya.Box(
            -l / 2,
            -npp_d - w / 2 - npp_width - y_increase - edge_slab_width / 2,
            l / 2,
            npp_d + w / 2 + npp_width + y_increase + edge_slab_width / 2,
        )
        wg3 = pya.Box(
            -l / 2,
            npp_d + w / 2 + y_increase,
            l / 2,
            npp_d + w / 2 + npp_width + y_increase,
        )
        wg4 = pya.Box(
            -l / 2,
            -npp_d - w / 2 - y_increase,
            l / 2,
            -npp_d - w / 2 - npp_width - y_increase,
        )

        self.cell.shapes(LayerSlab).insert(wg2)
        self.cell.shapes(LayerNPPN).insert(wg3)
        self.cell.shapes(LayerNPPN).insert(wg4)

        metal_routing = Path(
            [
                Point(
                    -l / 2,
                    -sw / 2
                    - contact_size
                    - metal_routing_distance_to_node
                    - 2 * vc_to_npp_exclusion
                    - y_increase,
                ),
                Point(
                    l / 2,
                    -sw / 2
                    - contact_size
                    - metal_routing_distance_to_node
                    - 2 * vc_to_npp_exclusion
                    - y_increase,
                ),
            ],
            metal_routing_width,
        )
        self.cell.shapes(LayerMN).insert(metal_routing)
        metal_routing = Path(
            [
                Point(
                    -l / 2,
                    sw / 2
                    + contact_size
                    + metal_routing_distance_to_node
                    + 2 * vc_to_npp_exclusion
                    + y_increase,
                ),
                Point(
                    l / 2,
                    sw / 2
                    + contact_size
                    + metal_routing_distance_to_node
                    + 2 * vc_to_npp_exclusion
                    + y_increase,
                ),
            ],
            metal_routing_width,
        )
        self.cell.shapes(LayerMN).insert(metal_routing)

        if folding_n > 0:
            dev = Box(
                wg_start,
                -sw / 2
                - contact_size
                - metal_routing_distance_to_node
                - 2 * vc_to_npp_exclusion
                - y_increase
                - metal_routing_width,
                wg_end,
                sw / 2
                + contact_size
                + metal_routing_distance_to_node
                + 2 * vc_to_npp_exclusion
                + y_increase
                + metal_routing_width,
            )
            self.cell.shapes(LayerDevRecN).insert(dev)

        t = Trans(0, False, Point(0, 0))
        text = Text("Waveguide Length=%.3fu" % (total_waveguide_length), t, 3 * w, -1)
        shape = self.cell.shapes(LayerDevRecN).insert(text)
