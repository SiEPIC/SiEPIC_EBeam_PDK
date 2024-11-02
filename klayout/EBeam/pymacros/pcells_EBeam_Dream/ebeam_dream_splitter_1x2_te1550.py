import pya
from pya import *


class ebeam_dream_splitter_1x2_te1550(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the ebeam_dream_splitter_1x2_te1550_BB

    Authors: Dream Photonics
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_dream_splitter_1x2_te1550, self).__init__()
        from SiEPIC.utils import get_technology_by_name

        self.technology_name = "EBeam"
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        from SiEPIC._globals import KLAYOUT_VERSION

        if KLAYOUT_VERSION >= 28:
            # Button to launch separate window
            self.param(
                "documentation", self.TypeCallback, "Open documentation in web browser"
            )

    def callback(self, layout, name, states):
        """Callback for PCell, to launch documentation viewer
        https://www.klayout.de/doc/code/class_PCellDeclaration.html#method9
        """
        if name == "documentation":
            url = "https://github.com/SiEPIC/SiEPIC_EBeam_PDK/wiki/Component-Library-description#dream-photonics-1x2-splitter"
            import webbrowser

            webbrowser.open_new(url)

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ebeam_dream_splitter_1x2_te1550_BB"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        # Load the geometries into KLayout
        import os

        dir_path = os.path.normpath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../gds/EBeam_Dream/"
            )
        )
        filename = os.path.join(dir_path, "ebeam_dream_splitter_1x2_te1550_BB.gds")
        tech_name = "EBeam"
        ly2 = pya.Layout()
        ly2.read(filename)
        top_cell = ly2.top_cell()
        top_cell.flatten(True)
        self.cell.copy_shapes(top_cell)
