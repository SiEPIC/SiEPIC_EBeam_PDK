import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_rib_phase_shifter(pya.PCellDeclarationHelper):
    # N-doped heater phase shifter in a rib waveguide
    # design by Guowu Zhang <guowu.zhang@mail.mcgill.ca>
    # and Lukas Chrostowski
    # based on Ref: R. Priti, Efficiency Improvement of an O-band SOI-MZI Thermo-optic Matrix Switch
    # Predicted performance:
    # resistance and power consumption using
    # 5 um NPP doping width, Length 150 um, rib width, 0.5 um and NPP to Silicon distance 1 um, the phase shifter are segmented to 4 parts
    # The estimated Resistance is ~ 140 ohm. The corresponding power consumption for pi phase shift is ~ 44 mW.
    # Simulation also shows that width of NPP region has influence on efficiency.
    # As an comparison, if NPP is 1 um, the power consumption for pi phase shift is ~ 23 mW.

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_rib_phase_shifter, self).__init__()
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
            "input_rib_width", self.TypeDouble, "Input Rib Width (um)", default=0.5
        )
        self.param(
            "input_slab_width", self.TypeDouble, "Input Slab Width (um)", default=2
        )
        self.param(
            "in_taper_length", self.TypeDouble, "Input Taper Length (um)", default=15
        )
        self.param("length", self.TypeDouble, "Phase Shifter Length (um)", default=150)
        self.param("width", self.TypeDouble, "Waveguide Width (um)", default=0.5)
        self.param("npp_width", self.TypeDouble, "Npp Width (um)", default=2)
        self.param(
            "npp_distance", self.TypeDouble, "Npp Edge to Si Waveguide (um)", default=2
        )
        self.param("segments", self.TypeInt, "Phase Shifter Segments", default=5)
        #    self.param("vc_dw", self.TypeDouble, "VC Offset", default = 5)
        self.param("vc_w", self.TypeDouble, "Contact via width", default=5)
        self.param(
            "vc_si_distance", self.TypeDouble, "VC Edge to Si Waveguide (um)", default=3
        )
        self.param(
            "overlay",
            self.TypeDouble,
            "Overlay accuracy (optical litho) (um)",
            default=1,
        )
        self.param(
            "overlay_ebl", self.TypeDouble, "Overlay accuracy (EBL) (um)", default=0.05
        )
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
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ebeam_rib_phase_shifter(L=" + ("%.3f" % self.length) + ")"

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

        ## define parameters for phase shifter

        # mask overlay accuracy
        overlay = to_itype(self.overlay, dbu)
        overlay_ebl = to_itype(self.overlay_ebl, dbu)

        ## define waveguide related parameters
        radius, adiab, bezier = 5 / dbu, 1, 0.2
        w = to_itype(self.width, dbu)  # waveguide width, default 0.5 um
        l = to_itype(self.length, dbu)  # pahse shifter length, default 150 um
        npp_d = to_itype(self.npp_distance, dbu)  # npp to edge of waveguide distance
        sw = 2 * npp_d + w  # twice of npp_d that is defined above
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

        ## define node related parameters
        contact_size = to_itype(self.vc_w, dbu)  # square NPP size, for VC purpose
        pin_text_size = to_itype(0.4, dbu)  # pin text size

        # define metal contact parameters
        metal_routing_width = to_itype(self.m_w, dbu)  # width of metal
        ps_sl_w = (
            sw + npp_width * 2 + 2 * overlay
        )  # define overall phase shifter 90nm slab width
        metal_routing_distance_to_node = metal_routing_width + ps_sl_w / 2
        vc_si_distance = to_itype(self.vc_si_distance, dbu)
        vc_to_npp_exclusion = to_itype(0, dbu)  # VC boundary to NPP boundary distance

        ## define strip to slab transfer taper parameters
        N = 100  # Number of points for the input/output slab taper
        order = 3  # input/output slab taper curve

        wg1 = pya.Box(-l / 2, -w / 2, l / 2, w / 2)
        wg2 = pya.Box(-l / 2, -ps_sl_w / 2, l / 2, ps_sl_w / 2)
        wg3 = pya.Box(-l / 2, npp_d + w / 2, l / 2, npp_d + w / 2 + npp_width)
        wg4 = pya.Box(-l / 2, -npp_d - w / 2, l / 2, -npp_d - w / 2 - npp_width)
        self.cell.shapes(LayerSiN).insert(wg1)

        self.cell.shapes(LayerNPPN).insert(wg3)
        self.cell.shapes(LayerNPPN).insert(wg4)

        if self.io_wg_type:
            in_slab = to_itype(self.input_slab_width, dbu)
        else:
            in_slab = in_rib

        if 1:
            self.cell.shapes(LayerSlab).insert(wg2)
            # add input strip taper
            pts = [
                Point(-l / 2 - in_taper, -in_rib / 2),
                Point(-l / 2, -w / 2),
                Point(-l / 2, w / 2),
                Point(-l / 2 - in_taper, in_rib / 2),
            ]
            # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
            self.cell.shapes(LayerSiN).insert(Polygon(pts))

            # add input slab taper
            pts = []
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        -l / 2 - in_taper + in_taper / N * i,
                        (in_slab - overlay_ebl * 2) / 2
                        + ((sw / 2 - (in_slab - overlay_ebl * 2)) / (N**order))
                        * (i**order),
                    )
                )
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        -l / 2 - in_taper + in_taper / N * (N - i),
                        -(in_slab - overlay_ebl * 2) / 2
                        - ((sw / 2 - (in_slab - overlay_ebl * 2)) / (N**order))
                        * ((N - i) ** order),
                    )
                )
            self.cell.shapes(LayerSlab).insert(Polygon(pts))

            # add output strip taper
            pts = [
                Point(l / 2 + in_taper, -in_rib / 2),
                Point(l / 2, -w / 2),
                Point(l / 2, w / 2),
                Point(l / 2 + in_taper, in_rib / 2),
            ]
            # wg2 = pya.Box(-l/2,-4/2/dbu,l/2,4/2/dbu)
            self.cell.shapes(LayerSiN).insert(Polygon(pts))

            # cubic taper
            pts = []
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        l / 2 + in_taper - in_taper / N * i,
                        (in_slab - overlay_ebl * 2) / 2
                        + ((sw / 2 - (in_slab - overlay_ebl * 2)) / (N**order))
                        * (i**order),
                    )
                )
            for i in range(0, N + 1):
                pts.append(
                    Point(
                        l / 2 + in_taper / N * i,
                        -(in_slab - overlay_ebl * 2) / 2
                        - ((sw / 2 - (in_slab - overlay_ebl * 2)) / (N**order))
                        * ((N - i) ** order),
                    )
                )
            self.cell.shapes(LayerSlab).insert(Polygon(pts))

            from SiEPIC._globals import PIN_LENGTH as pin_length

            # Pin on the left side:
            p1 = [
                Point(-l / 2 - in_taper + pin_length / 2, 0),
                Point(-l / 2 - in_taper - pin_length / 2, 0),
            ]
            p1c = Point(-l / 2 - in_taper, 0)
            self.set_p1 = p1c
            self.p1 = p1c
            pin = Path(p1, in_rib)
            self.cell.shapes(LayerPinRecN).insert(pin)
            t = Trans(Trans.R0, -l / 2 - in_taper, 0)
            text = Text("pin1", t)
            shape = self.cell.shapes(LayerPinRecN).insert(text)
            shape.text_size = pin_text_size

            # Pin on the right side:
            p2 = [
                Point(l / 2 + in_taper - pin_length / 2, 0),
                Point(l / 2 + in_taper + pin_length / 2, 0),
            ]
            p2c = Point(l / 2 + in_taper, 0)
            self.set_p2 = p2c
            self.p2 = p2c
            pin = Path(p2, in_rib)
            self.cell.shapes(LayerPinRecN).insert(pin)
            t = Trans(Trans.R0, l / 2 + in_taper, 0)
            text = Text("pin2", t)
            shape = self.cell.shapes(LayerPinRecN).insert(text)
            shape.text_size = pin_text_size

        for i in range(0, self.segments + 1):
            vc_temp_upper = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 + vc_to_npp_exclusion,
                w / 2 + vc_si_distance,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                - vc_to_npp_exclusion,
                w / 2 + vc_si_distance + contact_size,
            )
            self.cell.shapes(LayerVCN).insert(vc_temp_upper)
            wg_temp_upper = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 - overlay,
                sw / 2,
                (l - contact_size) / self.segments * i - l / 2 + contact_size + overlay,
                w / 2 + vc_si_distance + contact_size + overlay,
            )
            self.cell.shapes(LayerNPPN).insert(wg_temp_upper)
            wg_temp_upper = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 - 2 * overlay,
                sw / 2,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                + 2 * overlay,
                w / 2 + vc_si_distance + contact_size + 2 * overlay,
            )
            self.cell.shapes(LayerSlab).insert(wg_temp_upper)

            vc_temp_lower = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 + vc_to_npp_exclusion,
                -w / 2 - vc_si_distance,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                - vc_to_npp_exclusion,
                -w / 2 - vc_si_distance - contact_size,
            )
            self.cell.shapes(LayerVCN).insert(vc_temp_lower)
            wg_temp_lower = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 - overlay,
                -sw / 2,
                (l - contact_size) / self.segments * i - l / 2 + contact_size + overlay,
                -(w / 2 + vc_si_distance + contact_size + overlay),
            )
            self.cell.shapes(LayerNPPN).insert(wg_temp_lower)
            wg_temp_lower = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 - 2 * overlay,
                -sw / 2,
                (l - contact_size) / self.segments * i
                - l / 2
                + contact_size
                + 2 * overlay,
                -(w / 2 + vc_si_distance + contact_size + 2 * overlay),
            )
            self.cell.shapes(LayerSlab).insert(wg_temp_lower)

            metal_temp = pya.Box(
                (l - contact_size) / self.segments * i - l / 2 - overlay,
                -(w / 2 + vc_si_distance + contact_size + 1 * overlay)
                - metal_routing_distance_to_node * (i % 2),
                (l - contact_size) / self.segments * i - l / 2 + contact_size + overlay,
                w / 2
                + vc_si_distance
                + contact_size
                + 1 * overlay
                + metal_routing_distance_to_node * ((i + 1) % 2),
            )
            self.cell.shapes(LayerMN).insert(metal_temp)

        metal_routing = Path(
            [
                Point(-l / 2, -sw / 2 - metal_routing_distance_to_node - contact_size),
                Point(l / 2, -sw / 2 - metal_routing_distance_to_node - contact_size),
            ],
            metal_routing_width,
        )
        self.cell.shapes(LayerMN).insert(metal_routing)
        metal_routing = Path(
            [
                Point(-l / 2, sw / 2 + metal_routing_distance_to_node + contact_size),
                Point(l / 2, sw / 2 + metal_routing_distance_to_node + contact_size),
            ],
            metal_routing_width,
        )
        self.cell.shapes(LayerMN).insert(metal_routing)

        dev = Box(
            -l / 2 - in_taper,
            -sw / 2
            - metal_routing_distance_to_node
            - contact_size
            - metal_routing_width,
            +l / 2 + in_taper,
            sw / 2
            + metal_routing_distance_to_node
            + contact_size
            + metal_routing_width,
        )

        self.cell.shapes(LayerDevRecN).insert(dev)
