from pya import *
import pya


class Wireguide(pya.PCellDeclarationHelper):
    """
    RIT Integrated Photonics Group of Stefan Preble (Karl McNulty)
    new wireguide class (essentially the metal path equivalent to a waveguide but no bend is allowed)
    """

    def __init__(self):
        # Important: initialize the super class
        super(Wireguide, self).__init__()
        # declare the parameters
        from SiEPIC.utils import get_technology_by_name

        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param(
            "path",
            self.TypeShape,
            "Path",
            default=DPath([DPoint(0, 0), DPoint(10, 0), DPoint(10, 10)], 0.5),
        )
        self.radius = 0
        self.param("width", self.TypeDouble, "Width", default=0.5)
        self.adiab = False
        self.param("layers", self.TypeList, "Layers", default=["M2_router"])
        self.param("widths", self.TypeList, "Widths", default=[5])
        self.param("offsets", self.TypeList, "Offsets", default=[0])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Wireguide_%s" % self.path

    def coerce_parameters_impl(self):
        return

    def can_create_from_shape_impl(self):
        return self.shape.is_path()

    def transformation_from_shape_impl(self):
        return Trans(Trans.R0, 0, 0)

    def parameters_from_shape_impl(self):
        self.path = self.shape.dpath

    def produce_impl(self):
        from SiEPIC.utils import (
            arc_xy,
            arc_bezier,
            angle_vector,
            angle_b_vectors,
            inner_angle_b_vectors,
        )
        import pya
        from SiEPIC.extend import to_itype

        # print("EBeam.Wireguide")

        from SiEPIC.utils import get_technology_by_name

        TECHNOLOGY = get_technology_by_name("EBeam")

        dbu = self.layout.dbu
        wg_width = to_itype(self.width, dbu)
        path = self.path.to_itype(dbu)

        if not (
            len(self.layers) == len(self.widths)
            and len(self.layers) == len(self.offsets)
            and len(self.offsets) == len(self.widths)
        ):
            raise Exception(
                "There must be an equal number of layers, widths and offsets"
            )
        path.unique_points()
        turn = 0
        for lr in range(0, len(self.layers)):
            layer = self.layout.layer(TECHNOLOGY[self.layers[lr]])

            width = to_itype(self.widths[lr], dbu)
            offset = to_itype(self.offsets[lr], dbu)

            pts = path.get_points()
            wg_pts = [pts[0]]
            for i in range(1, len(pts) - 1):
                turn = (
                    (angle_b_vectors(pts[i] - pts[i - 1], pts[i + 1] - pts[i]) + 90)
                    % 360
                    - 90
                ) / 90
                dis1 = pts[i].distance(pts[i - 1])
                dis2 = pts[i].distance(pts[i + 1])
                angle = angle_vector(pts[i] - pts[i - 1]) / 90
                pt_radius = self.radius
                # determine the radius, based on how much space is available
                if len(pts) == 3:
                    pt_radius = min(dis1, dis2, pt_radius)
                else:
                    if i == 1:
                        if dis1 <= pt_radius:
                            pt_radius = dis1
                    elif dis1 < 2 * pt_radius:
                        pt_radius = dis1 / 2
                    if i == len(pts) - 2:
                        if dis2 <= pt_radius:
                            pt_radius = dis2
                    elif dis2 < 2 * pt_radius:
                        pt_radius = dis2 / 2
                # wireguide bends:
                if self.adiab:
                    wg_pts += (
                        Path(
                            arc_bezier(
                                pt_radius,
                                270,
                                270
                                + inner_angle_b_vectors(
                                    pts[i - 1] - pts[i], pts[i + 1] - pts[i]
                                ),
                                self.bezier,
                                DevRec="DevRec" in self.layers[lr],
                                dbu=dbu,
                            ),
                            0,
                        )
                        .transformed(Trans(angle, turn < 0, pts[i]))
                        .get_points()
                    )
                else:
                    wg_pts += (
                        Path(
                            arc_xy(
                                -pt_radius,
                                pt_radius,
                                pt_radius,
                                270,
                                270
                                + inner_angle_b_vectors(
                                    pts[i - 1] - pts[i], pts[i + 1] - pts[i]
                                ),
                                DevRec="DevRec" in self.layers[lr],
                                dbu=dbu,
                            ),
                            0,
                        )
                        .transformed(Trans(angle, turn < 0, pts[i]))
                        .get_points()
                    )
            wg_pts += [pts[-1]]
            wg_pts = pya.Path(wg_pts, 0).unique_points().get_points()
            wg_polygon = Path(wg_pts, wg_width)
            self.cell.shapes(layer).insert(wg_polygon)  # insert the wireguide

            # if self.layout.layer(TECHNOLOGY['Wireguide']) == layer:
            waveguide_length = wg_polygon.area() / self.width * dbu**2

        pts = path.get_points()
        LayerPinRecN = self.layout.layer(TECHNOLOGY["PinRecM"])

        # insert pins to wireguide
        t1 = Trans(angle_vector(pts[0] - pts[1]) / 90, False, pts[0])
        self.cell.shapes(LayerPinRecN).insert(
            Path([Point(-50, 0), Point(50, 0)], wg_width).transformed(t1)
        )
        self.cell.shapes(LayerPinRecN).insert(Text("pin1", t1, 0.3 / dbu, -1))

        t = Trans(angle_vector(pts[-1] - pts[-2]) / 90, False, pts[-1])
        self.cell.shapes(LayerPinRecN).insert(
            Path([Point(-50, 0), Point(50, 0)], wg_width).transformed(t)
        )
        self.cell.shapes(LayerPinRecN).insert(Text("pin2", t, 0.3 / dbu, -1))

        LayerDevRecN = self.layout.layer(TECHNOLOGY["DevRec"])

        # Compact model information
        angle_vec = angle_vector(pts[0] - pts[1]) / 90
        halign = 0  # left
        angle = 0
        pt2 = pts[0]
        pt3 = pts[0]
        if angle_vec == 0:  # horizontal
            halign = 2  # right
            angle = 0
            pt2 = pts[0] + Point(0, wg_width)
            pt3 = pts[0] + Point(0, -wg_width)
        if angle_vec == 2:  # horizontal
            halign = 0  # left
            angle = 0
            pt2 = pts[0] + Point(0, wg_width)
            pt3 = pts[0] + Point(0, -wg_width)
        if angle_vec == 1:  # vertical
            halign = 2  # right
            angle = 1
            pt2 = pts[0] + Point(wg_width, 0)
            pt3 = pts[0] + Point(-wg_width, 0)
        if angle_vec == -1:  # vertical
            halign = 0  # left
            angle = 1
            pt2 = pts[0] + Point(wg_width, 0)
            pt3 = pts[0] + Point(-wg_width, 0)
