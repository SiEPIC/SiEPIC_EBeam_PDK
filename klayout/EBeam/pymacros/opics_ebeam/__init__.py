"""OID: orthogonal ID for polarization, 1=TE (first mode)"""

from copy import deepcopy
from pathlib import Path
import numpy as np
from SiEPIC.opics.components import componentModel
from SiEPIC.opics.utils import LUT_reader
from numpy import complex128, ndarray
from pathlib import PosixPath

datadir = Path(str(Path(__file__).parent.parent.parent)) / "CML/EBeam/source_data"


class contra_directional_coupler(componentModel):
    """
    Bragg Grating-assisted Contra Directional Coupler.
    This component operates as an optical add-drop multiplexer (AODM) or filter.

    Model schematic:
    ~~~~~~~~~~~~~~~

    0 ┌───┐             ┌───┐ 2
      └───┼──┐       ┌──┼───┘
          └──┼───────┼──┘
             │┼┼┼┼┼┼┼│
          ┌──┼───────┼──┐
      ┌───┼──┘       └──┼───┐
    1 └───┘             └───┘ 3
    """

    cls_attrs = {
        "wg1_width": 0,
        "wg2_width": 0,
        "corrugation1_width": 0,
        "corrugation2_width": 0,
        "gap": 0,
        "grating_period": 0,
        "number_of_periods": 0,
        "sinusoidal": 0,
        "apodization_index": 0,
        "rib": 0,
    }
    valid_OID = [1]
    ports = 4

    def __init__(
        self,
        f: ndarray = None,
        wg1_width: float = 560e-9,
        wg2_width: float = 440e-9,
        corrugation1_width: float = 50e-9,
        corrugation2_width: float = 25e-9,
        gap: float = 100e-9,
        grating_period: float = 316e-9,
        number_of_periods: int = 1000,
        sinusoidal: bool = False,
        apodization_index: float = 10.0,
        rib: bool = False,
        OID: int = 1,
    ) -> None:
        data_folder = datadir / "contraDC"
        filename = "contraDC.xml"
        """
        file_search =  "w1=" + "%.0f"%(wg1_width*1e9) + ",w2=" + "%.0f"%(wg2_width*1e9) + ",dW1=" + "%.0f"%(corrugation1_width*1e9) + ",dW2=" + "%.0f"%(corrugation2_width*1e9) +  ",gap=" + "%.0f"%(gap*1e9) + ",p=" + "%.1f"%(grating_period*1e9) + ",N=" + "%.0f"%(number_of_periods) + ",s=" + str(1 if sinusoidal else 0) +  ",a=" + "%.2f"%apodization_index +  ",rib=" + str(1 if rib else 0) + ",pol=" + str(OID-1)
        import os, fnmatch
        files = fnmatch.filter(os.listdir(data_folder), file_search + '*')
        if not files:
            raise Exception ('The contra-directional coupler Compact Model Library does not have data for the chosen parameters. Requested file: ' + file_search);
        else:
            filename = files[0] # pick the first one. Could be improved to pick the one with the highest resolution, etc., or give people the choice.
            print('contra directional coupler, data file: %s' % filename)    
        """
        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["wg1_width"] = wg1_width
        LUT_attrs_["wg2_width"] = wg2_width
        LUT_attrs_["corrugation1_width"] = corrugation1_width
        LUT_attrs_["corrugation2_width"] = corrugation2_width
        LUT_attrs_["gap"] = gap
        LUT_attrs_["grating_period"] = grating_period
        LUT_attrs_["number_of_periods"] = number_of_periods
        LUT_attrs_["sinusoidal"] = sinusoidal
        LUT_attrs_["apodization_index"] = apodization_index
        LUT_attrs_["rib"] = rib

        super().__init__(
            f=f,
            data_folder=data_folder,
            filename=filename,
            nports=4,
            sparam_attr="contra_directional_coupler",
            **LUT_attrs_,
        )

        if OID in self.valid_OID:
            self.s = self.load_sparameters(data_folder, filename, verbose=True)
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
        self.component_id = "contra_directional_coupler"


class ebeam_bdc_te1550(componentModel):
    """
    50/50% broadband directional 3-dB couplers. Two 3-dB couplers can be used to make an unbalanced Mach-Zehnder Interferometer (MZI),
    showing a large extinction ratio. The advantage of this device compared to the Y-Branch is that it has 2x2 ports,
    thus the MZI has two outputs. Compared to the directional coupler, it is less wavelength sensitive.

    Model schematic:
    ~~~~~~~~~~~~~~~

    0 ┌───┐             ┌───┐ 2
      └───┼──┐       ┌──┼───┘
          └──┼───────┼──┘
             │┼┼┼┼┼┼┼│
          ┌──┼───────┼──┐
      ┌───┼──┘       └──┼───┐
    1 └───┘             └───┘ 3
    """

    cls_attrs = {"height": 0, "width": 0}
    valid_OID = [1]
    ports = 4

    def __init__(
        self,
        f: ndarray = None,
        height: float = 220e-9,
        width: float = 500e-9,
        OID: int = 1,
    ) -> None:
        data_folder = datadir / "bdc_TE_source"
        filename = "bdc_lookup_table.xml"

        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["height"] = height
        LUT_attrs_["width"] = width
        super().__init__(
            f=f,
            data_folder=data_folder,
            filename=filename,
            nports=4,
            sparam_attr="bdc_sparam",
            **LUT_attrs_,
        )
        if OID in self.valid_OID:
            self.s = self.load_sparameters(data_folder, filename)
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
        self.component_id = "ebeam_bdc_te1550"


class DC_temp(componentModel):
    """
    The directional coupler is commonly used for splitting and combining light in photonics.
    It consists of two parallel waveguides where the coupling coefficient is influenced by the
    waveguide length and the distance between waveguides.

    Model schematic:
    ~~~~~~~~~~~~~~~

    1                      3
     ##                 ##
      ###             ###
        ###         ###
          ###     ###
              ###

    0 ###################  2
    """

    cls_attrs = {"Lc": 0}
    valid_OID = [1]
    ports = 4

    def __init__(self, f=None, Lc=0, OID=1):
        data_folder = datadir / "ebeam_dc_te1550"
        filename = "dc_map.xml"

        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["Lc"] = Lc
        super().__init__(
            f=f,
            data_folder=data_folder,
            filename=filename,
            nports=4,
            sparam_attr="s-param",
            **LUT_attrs_,
        )
        if OID in self.valid_OID:
            self.s = self.load_sparameters(data_folder, filename)
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
        self.component_id = "Ebeam_DC"


class DC_halfring(componentModel):
    """
    Models evanescent coupling region between a straight waveguide and a bent radius of length pi*radius um. Useful for filters, sensors.

    Model schematic:
    ~~~~~~~~~~~~~~~

    1                      3
     ##                 ##
      ###             ###
        ###         ###
          ###     ###
              ###

    0 ###################  2
    """

    cls_attrs = {
        "CoupleLength": 0,
        "gap": 100e-9,
        "radius": 5e-6,
        "thickness": 220e-9,
        "width": 500e-9,
    }
    valid_OID = [1]
    ports = 4

    def __init__(
        self,
        f: ndarray = None,
        CoupleLength: int = 0,
        gap: float = 100e-9,
        radius: float = 5e-6,
        thickness: float = 220e-9,
        width: float = 500e-9,
        OID: int = 1,
    ) -> None:
        data_folder = datadir / "ebeam_dc_halfring_straight"
        filename = "te_ebeam_dc_halfring_straight.xml"

        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["CoupleLength"] = CoupleLength
        LUT_attrs_["gap"] = gap
        LUT_attrs_["radius"] = radius
        LUT_attrs_["thickness"] = thickness
        LUT_attrs_["width"] = width

        super().__init__(
            f=f,
            data_folder=data_folder,
            filename=filename,
            nports=4,
            sparam_attr="s-param",
            **LUT_attrs_,
        )
        if OID in self.valid_OID:
            self.s = self.load_sparameters(data_folder, filename)
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
        self.component_id = "Ebeam_DC_halfring"


class GC(componentModel):
    """
    Fully-etched fibre-waveguide grating couplers with sub-wavelength gratings showing high coupling efficiency as well as low
    back reflections for both transverse electric (TE) and transverse magnetic (TM) modes. EBeam fabrication cost is reduced
    by ~2-3X when eliminating the shallow etch.

    Model schematic:
    ~~~~~~~~~~~~~~~~
                     |
        ◄──────    │ │
               │ │ │ │
       ┌───────┤ │ │ │
    1  └───────┤ │ │ │  0
               │ │ │ │
                   │ │
                     |
    """

    cls_attrs = {"deltaw": 0, "height": 2.2e-07}
    valid_OID = [1]
    ports = 2

    def __init__(
        self, f: ndarray = None, deltaw: int = 0, height: float = 2.2e-07, OID: int = 1
    ) -> None:
        data_folder = datadir / "gc_source"
        filename = "GC_TE_lookup_table.xml"

        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["deltaw"] = deltaw
        LUT_attrs_["height"] = height
        super().__init__(
            f=f,
            nports=2,
            data_folder=data_folder,
            filename=filename,
            sparam_attr="gc_sparam",
            **LUT_attrs_,
        )
        if OID in self.valid_OID:
            self.s = self.load_sparameters(data_folder, filename)
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))

        self.component_id = "Ebeam_GC"


class Multimode(componentModel):
    valid_OID = [1, 2]
    ports = 2

    def __init__(self, f=None, OID=1):
        super().__init__(f, "", "")
        if OID in self.valid_OID and OID == 1:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
            self.s[1, 0] = self.s[0, 1] = -2 * np.ones((self.f.shape[0]))
        elif OID in self.valid_OID and OID == 2:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
            self.s[1, 0] = self.s[0, 1] = -5 * np.ones((self.f.shape[0]))
        self.component_id = "Ebeam_multimode"


class Terminator(componentModel):
    """
    This component is used to terminate a waveguide. This terminator is a nano-taper that spreads
    the light into the oxide and is used for efficient edge coupling. Even if a waveguide crosses near
    this taper end, the reflection is minimal. This is included in this model, 1 µm away, therefore,
    the model is a worst-case reflection. To terminate unused ports on components to avoid reflections,
    refer to Disconnected Waveguides.

    Model schematic:
    ~~~~~~~~~~~~~~~


      ┌┬──┐
    0 ││  ├────────┐
      ││  ├────────┘
      └┴──┘



    """

    valid_OID = [1]
    ports = 2

    def __init__(self, f=None, OID=1):
        data_folder = datadir / "ebeam_terminator_te1550"
        filename = "ebeam_terminator_te1550.npz"
        super().__init__(f=f, data_folder=data_folder, filename=filename)
        if OID in self.valid_OID:
            self.s = self.load_sparameters(data_folder=data_folder, filename=filename)
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
        self.component_id = "Ebeam_Terminator"


class TunableWG(componentModel):
    """
    Waveguides are components that guide waves. Although these are individual components that can
    be adjusted for use, it is recommended to draw paths in KLayout and convert them to waveguides
    using the built-in SiEPIC features.

    The behavior of tunable waveguides can be adjusted by modifying the `power` parameter.

    Model schematic:
    ~~~~~~~~~~~~~~~

    0 ┌─────────┐ 1
      └─────────┘

    """

    cls_attrs = {"power": 0}
    valid_OID = [1, 2]
    ports = 2

    def __init__(
        self,
        f: ndarray = None,
        length: float = 5e-6,
        power: float = 0e-3,
        loss: int = 700,
        OID: int = 1,
    ) -> None:
        data_folder = datadir / "tunable_wg"
        filename = "wg_strip_tunable.xml"
        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["power"] = power

        if OID in self.valid_OID:
            self.s = self.load_sparameters(
                length=length,
                data_folder=data_folder,
                filename=filename,
                neff=None,
                ng=None,
                loss=loss,
            )
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
        self.component_id = "Ebeam_TunableWG"

    def load_sparameters(
        self,
        length: float,
        data_folder: PosixPath,
        filename: str,
        neff: float,
        ng: float,
        loss: int,
    ) -> ndarray:
        """overrides read s_parameters"""

        sfilename, _, _ = LUT_reader(data_folder, filename, self.componentParameters)
        self.sparam_file = sfilename[-1]
        filepath = data_folder / sfilename[-1]

        # Read info from waveguide s-param file
        with open(filepath, "r") as f:
            coeffs = f.readline().split()

        # Initialize array to hold s-params
        temp_s_ = np.zeros((len(self.f), self.nports, self.nports), dtype=complex128)

        alpha = loss / (20 * np.log10(np.exp(1)))

        # calculate angular frequency from frequency
        w = np.asarray(self.f) * 2 * np.pi

        # calculate center wavelength, effective index, group index, group dispersion
        lam0, ne, ng_, nd = (
            float(coeffs[0]),
            float(coeffs[1]),
            float(coeffs[3]),
            float(coeffs[5]),
        )

        if neff:
            ne = neff
        if ng:
            ng = ng
        else:
            ng = ng_

        # calculate angular center frequency
        w0 = (2 * np.pi * self.C) / lam0

        # calculation of K
        K = (
            2 * np.pi * ne / lam0
            + (ng / self.C) * (w - w0)
            - (nd * lam0**2 / (4 * np.pi * self.C)) * ((w - w0) ** 2)
        )

        # compute s-matrix from K and waveguide length
        temp_s_[:, 0, 1] = temp_s_[:, 1, 0] = np.exp(
            -alpha * length + (K * length * 1j)
        )

        s = temp_s_
        self.ng_ = ng
        self.alpha_ = alpha
        self.ne_ = ne
        self.nd_ = nd

        return s


class Waveguide(componentModel):
    """
    Waveguides are components that guide waves. Although these are individual components that can
    be adjusted for use, it is recommended to draw paths in KLayout and convert them to waveguides
    using the built-in SiEPIC features.

    Model schematic:
    ~~~~~~~~~~~~~~~~

    0 ┌─────────┐ 1
      └─────────┘

    """

    cls_attrs = {"length": 0e-6, "height": 220e-9, "width": 500e-9}
    valid_OID = [1, 2]
    ports = 2

    def __init__(
        self,
        f: ndarray = None,
        length: float = 5e-6,
        height: float = 220e-9,
        width: float = 500e-9,
        loss: int = 700,
        OID: int = 1,
    ) -> None:
        data_folder = datadir / "wg_integral_source"
        filename = "wg_strip_lookup_table.xml"

        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["height"] = height
        LUT_attrs_["width"] = width

        # length is not part of LUT attributes
        del LUT_attrs_["length"]

        super().__init__(
            f,
            length=length,
            data_folder=data_folder,
            filename=filename,
            loss=loss,
            **LUT_attrs_,
        )

        if OID in self.valid_OID:
            self.s = self.load_sparameters(
                length=length,
                data_folder=data_folder,
                filename=filename,
                neff=None,
                ng=None,
                loss=loss,
            )
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))

        self.component_id = "Ebeam_WG"

    def load_sparameters(
        self,
        length: float,
        data_folder: PosixPath,
        filename: str,
        neff: float,
        ng: float,
        loss: int,
    ) -> ndarray:
        """overrides read s_parameters"""

        sfilename, _, _ = LUT_reader(data_folder, filename, self.componentParameters)
        self.sparam_file = sfilename[-1]
        filepath = data_folder / sfilename[-1]

        # Read info from waveguide s-param file
        with open(filepath, "r") as f:
            coeffs = f.readline().split()

        # Initialize array to hold s-params
        temp_s_ = np.zeros((len(self.f), self.nports, self.nports), dtype=complex128)

        alpha = loss / (20 * np.log10(np.exp(1)))

        # calculate angular frequency from frequency
        w = np.asarray(self.f) * 2 * np.pi

        # calculate center wavelength, effective index, group index, group dispersion
        lam0, ne, ng_, nd = (
            float(coeffs[0]),
            float(coeffs[1]),
            float(coeffs[3]),
            float(coeffs[5]),
        )

        if neff:
            ne = neff
        if ng:
            ng = ng
        else:
            ng = ng_

        # calculate angular center frequency
        w0 = (2 * np.pi * self.C) / lam0

        # calculation of K
        K = (
            2 * np.pi * ne / lam0
            + (ng / self.C) * (w - w0)
            - (nd * lam0**2 / (4 * np.pi * self.C)) * ((w - w0) ** 2)
        )

        # compute s-matrix from K and waveguide length
        temp_s_[:, 0, 1] = temp_s_[:, 1, 0] = np.exp(
            -alpha * length + (K * length * 1j)
        )

        s = temp_s_
        self.ng_ = ng
        self.alpha_ = alpha
        self.ne_ = ne
        self.nd_ = nd

        return s


class Y(componentModel):
    r"""
    50/50 3dB splitter. Useful for splitting light, Mach-Zehner Interferometers, etc.
    The layout parameters for the device were taken from the journal paper below, and implemented in EBeam lithography.

    Model schematic:
    ~~~~~~~~~~~~~~~~

              ┌─────────┐ 1
              ├─┼───────┘
              │ │
    0 ┌───────┼─┤
      └───────┼─┤
              │ │
              ├─┼───────┐ 2
              └─────────┘

    """

    cls_attrs = {"height": 220e-9, "width": 500e-9}
    valid_OID = [1]
    ports = 3

    def __init__(
        self,
        f: ndarray = None,
        height: float = 220e-9,
        width: float = 500e-9,
        OID: int = 1,
    ) -> None:
        data_folder = datadir / "y_branch_source"
        filename = "y_lookup_table.xml"
        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["height"] = height
        LUT_attrs_["width"] = width

        # print(LUT_attrs_)
        super().__init__(
            f=f,
            nports=3,
            data_folder=data_folder,
            filename=filename,
            sparam_attr="y_sparam",
            **LUT_attrs_,
        )
        if OID in self.valid_OID:
            self.s = self.load_sparameters(data_folder, filename)
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
        self.component_id = "Ebeam_Y"


class Switch(componentModel):
    """2x2 tunable optical switch component. Useful for switching the input optical power between two output ports."""

    cls_attrs = {"power": 0}
    valid_OID = [1]
    ports = 4

    def __init__(self, f: ndarray = None, power: float = 0e-3, OID: int = 1) -> None:
        data_folder = datadir / "2x2_switch"
        filename = "2x2_switch.xml"

        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["power"] = power
        super().__init__(f, data_folder, filename, 4, "switch_sparam", **LUT_attrs_)
        if OID in self.valid_OID:
            self.s = self.load_sparameters(data_folder, filename)
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))
        self.component_id = "Ebeam_switch"


class ebeam_wg_integral_1550(componentModel):
    """
    Waveguides are components that guide waves. Although these are individual components that can
    be adjusted for use, it is recommended to draw paths in KLayout and convert them to waveguides
    using the built-in SiEPIC features.

    Model schematic:
    ~~~~~~~~~~~~~~~~

    0 ┌─────────┐ 1
      └─────────┘

    """

    cls_attrs = {"wg_length": 0e-6, "wg_height": 220e-9, "wg_width": 500e-9}
    valid_OID = [1, 2]
    ports = 2

    def __init__(
        self,
        f: ndarray = None,
        wg_length: float = 5e-6,
        wg_height: float = 220e-9,
        wg_width: float = 500e-9,
        loss: int = 700,
        OID: int = 1,
    ) -> None:
        data_folder = datadir / "wg_integral_source"
        filename = "wg_strip_lookup_table.xml"

        LUT_attrs_ = deepcopy(self.cls_attrs)
        LUT_attrs_["wg_height"] = wg_height
        LUT_attrs_["wg_width"] = wg_width

        # wg_length is not part of LUT attributes
        del LUT_attrs_["wg_length"]

        super().__init__(
            f,
            length=wg_length,
            data_folder=data_folder,
            filename=filename,
            loss=loss,
            **LUT_attrs_,
        )

        if OID in self.valid_OID:
            self.s = self.load_sparameters(
                length=wg_length,
                data_folder=data_folder,
                filename=filename,
                neff=None,
                ng=None,
                loss=loss,
            )
        else:
            self.s = np.zeros((self.f.shape[0], self.ports, self.ports))

        self.component_id = "Ebeam_WG"

    def load_sparameters(
        self,
        length: float,
        data_folder: PosixPath,
        filename: str,
        neff: float,
        ng: float,
        loss: int,
    ) -> ndarray:
        """overrides read s_parameters"""

        sfilename, _, _ = LUT_reader(data_folder, filename, self.componentParameters)
        self.sparam_file = sfilename[-1]
        filepath = data_folder / sfilename[-1]

        # Read info from waveguide s-param file
        with open(filepath, "r") as f:
            coeffs = f.readline().split()

        # Initialize array to hold s-params
        temp_s_ = np.zeros((len(self.f), self.nports, self.nports), dtype=complex128)

        alpha = loss / (20 * np.log10(np.exp(1)))

        # calculate angular frequency from frequency
        w = np.asarray(self.f) * 2 * np.pi

        # calculate center wavelength, effective index, group index, group dispersion
        lam0, ne, ng_, nd = (
            float(coeffs[0]),
            float(coeffs[1]),
            float(coeffs[3]),
            float(coeffs[5]),
        )

        if neff:
            ne = neff
        if ng:
            ng = ng
        else:
            ng = ng_

        # calculate angular center frequency
        w0 = (2 * np.pi * self.C) / lam0

        # calculation of K
        K = (
            2 * np.pi * ne / lam0
            + (ng / self.C) * (w - w0)
            - (nd * lam0**2 / (4 * np.pi * self.C)) * ((w - w0) ** 2)
        )

        # compute s-matrix from K and waveguide length
        temp_s_[:, 0, 1] = temp_s_[:, 1, 0] = np.exp(
            -alpha * length + (K * length * 1j)
        )

        s = temp_s_
        self.ng_ = ng
        self.alpha_ = alpha
        self.ne_ = ne
        self.nd_ = nd

        return s


component_factory = dict(
    contra_directional_coupler=contra_directional_coupler,
    BDC=ebeam_bdc_te1550,
    ebeam_bdc_te1550=ebeam_bdc_te1550,
    DC_halfring=DC_halfring,
    # DC_temp=DC_temp,
    GC=GC,
    # Multimode=Multimode,
    # Path=Path,
    Switch=Switch,
    # Terminator=Terminator,
    TunableWG=TunableWG,
    Waveguide=Waveguide,
    Y=Y,
    ebeam_y_1550=Y,
    ebeam_gc_te1550=GC,
    GC_TE_1550_8degOxide_BB=GC,
    ebeam_wg_integral_1550=ebeam_wg_integral_1550,
)

components_list = list(component_factory.keys())
__all__ = components_list
__version__ = "0.4.11"

if __name__ == "__main__":
    import SiEPIC.opics as op

    w = np.linspace(1.52, 1.58, 3) * 1e-6
    f = op.C / w
    c = ebeam_bdc_te1550(f=f)
    s = c.get_data()

    print(components_list)
    print(datadir)
