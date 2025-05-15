'''
Racetrack resonator using Euler bends

by Lukas Chrostowski
using Euler bends implemented by Evan Jonker

'''


import pya
from pya import *
from SiEPIC.utils import get_technology_by_name

def euler_bend(radius, p=0.25, DevRec=None, dbu=0.001, debug=False):
    '''Function to create points for a 180 degree euler bend of 
    optional radius and with a user-specified bend parameter 'p'.
    Inspired from GDS factory code [1] and the 2019 Vogelbacher et al. paper:
    'Analysis of silicon nitride partial Euler waveguide bends' [2].
    
    [1] https://github.com/gdsfactory/gdsfactory/blob/main/gdsfactory/path.py
    [2] https://dx.doi.org/10.1364/oe.27.031394
    
        INPUTS:
            radius (float): desired effective radius 
            p (float): bend parameter, must be between 0.0 and 1.0
            
        by Evan Jonker
    '''
    from SiEPIC.utils import points_per_circle
    import numpy as np
    import scipy.integrate as integrate
    import pya

    N = points_per_circle(radius/1000, dbu=dbu)/4
    if DevRec:
        N = int(N / 3)
    else:
        N = int(N)
    if N < 5:
      N = 100

    # Internal variables
    angle = 180
    npoints = 300
    npoints = int(N)
    if debug:
        print("N = {}".format(npoints))
    R0 = 1
    alpha = np.radians(angle)
    Rp = R0 / np.sqrt(p * alpha)
    sp = R0 * np.sqrt(p * alpha)
    s0 = 2 * sp + Rp * alpha * (1 - p)

    # The minimum radius is Rp
    Rmin = Rp

    # Allocate points for euler-bend and circular sections
    num_pts_euler = int(np.round(sp / (s0 / 2) * npoints))
    num_pts_arc = npoints - num_pts_euler

    # Calculate [x,y] of euler-bend by numerically solving fresnel integrals
    s_euler = np.linspace(0, sp, num_pts_euler)
    xbend1 = np.zeros(num_pts_euler)
    ybend1 = np.zeros(num_pts_euler)
    for i, s_pt in enumerate(s_euler):
        xbend1[i], _ = integrate.quad(lambda t: np.cos((t/R0)**2 / 2), 0, s_pt)
        ybend1[i], _ = integrate.quad(lambda t: np.sin((t/R0)**2 / 2), 0, s_pt)

    # Determine the offset for the circular section
    xp, yp = xbend1[-1], ybend1[-1]
    dx = xp - Rp * np.sin(p * alpha / 2)
    dy = yp - Rp * (1 - np.cos(p * alpha / 2))

    # Calculate [x,y] for the circular-bend section
    s_arc = np.linspace(sp, s0 / 2, num_pts_arc)
    xbend2 = Rp * np.sin((s_arc - sp) / Rp + p * alpha / 2) + dx
    ybend2 = Rp * (1 - np.cos((s_arc - sp) / Rp + p * alpha / 2)) + dy

    # Join euler-bend and circular sections
    x = np.concatenate([xbend1, xbend2[1:]])
    y = np.concatenate([ybend1, ybend2[1:]])

    # Evaluate effective radius before re-scaling
    if angle == 90:
        Reff = x[-1] + y[-1]
    elif angle == 180:
        Reff = 2*y[-1]

    # Determine second half of the bend as the a mirror of the first
    points2 = np.array([np.flipud(x), np.flipud(Reff - y)]).T

    # Scale the curve to match the desired radius
    if angle == 90:
        scale = radius / Reff
    elif angle == 180:
        scale = 2*radius / Reff
    points = np.concatenate([np.array([x, y]).T[:-1], points2]) * scale
    
    if angle == 180:
        points = np.append(points, [[points[-1,0]+0.001, points[-1,1]]], axis=0)

    # Create array of "Point" types
    pts = []
    for i in range(len(points)):
        pts.append(pya.Point(points[i,0] - radius, points[i,1]))  

    if debug:
        print("Euler pts: {}".format(pts))
    
    return pts


class racetrack_euler(pya.PCellDeclarationHelper):
    """
    A racetrack resonator using Euler curve for the U-turn.
    """

    def __init__(self):
        # Important: initialize the super class
        super(racetrack_euler, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # Button to launch separate window
        self.param(
            "documentation", self.TypeCallback, "Open documentation in web browser"
        )
        #    self.param("simulation", self.TypeCallback, "Launch simulation GUI")

        # declare the parameters
        self.param("w", self.TypeDouble, "Waveguide Width (micron)", default=0.5)
        self.param("g", self.TypeDouble, "Coupler Gap (micron)", default=0.1)
        self.param("Lc", self.TypeDouble, "Coupler Length (micron)", default=10)
        self.param("r", self.TypeDouble, "Effective Bend Radius (micron)", default=5)
        self.param("p", self.TypeDouble, "Euler parameter, p", default=0.5)
        self.param("accuracy", self.TypeDouble, "Curve accuracy (micron)", default=0.005)
        self.param("silayer", self.TypeLayer, "Waveguide Layer", default=TECHNOLOGY["Si"])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"])

    def callback(self, layout, name, states):
        """Callback for PCell, to launch documentation viewer
        https://www.klayout.de/doc/code/class_PCellDeclaration.html#method9
        """
        if name == "documentation":
            url = "https://github.com/SiEPIC/SiEPIC_EBeam_PDK"
            import webbrowser

            webbrowser.open_new(url)

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "racetrack_euler("
            + (
                "%.3f-%.3f-%.3f-%.3f-%.3f"
                % (self.w, self.Lc, self.g, self.r, self.p)
            )
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce(self, layout, layers, parameters, cell):
        from packaging import version
        import SiEPIC

        if version.parse(SiEPIC.__version__) < version.parse("0.5.11"):
            raise Exception(
                "Errors",
                "This PCell requires SiEPIC-Tools version 0.5.11 or greater. You have %s"
                % SiEPIC.__version__,
            )

        # from SiEPIC.utils.geometry import bezier_cubic
        from SiEPIC.extend import to_itype
        from SiEPIC.utils.layout import make_pin

        self._layers = layers
        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)


        '''
        w = to_itype(self.w, dbu)
        g = to_itype(self.g, dbu)
        Lc = to_itype(self.Lc, dbu)
        from math import pi
        wg_Dpts = (
            bezier_cubic(
                pya.DPoint(self.Lc/2, 0),
                pya.DPoint(self.Lc/2, self.r*2),
                0,
                pi,
                self.a,
                self.b,
                accuracy=self.accuracy,
            )
            # + bezier_cubic(
            #     pya.DPoint(-self.Lc/2, 0),
            #     pya.DPoint(-self.Lc/2, self.r*2),
            #     pi,
            #     0,
            #     self.a,
            #     self.b,
            #     accuracy=self.accuracy,
            # )[::-1]
        )

        from SiEPIC.utils.geometry import translate_from_normal2
        wg_polygon = pya.DPolygon(wg_Dpts)
        #cell.shapes(LayerSi).insert(wg_polygon)


        # U-turn concept
        # 45º bezier (90º bezier but only 45º to where the radius is minimum)
        # 90º constant radius turn
        # 45º bezier turn
        a=.5
        # p =  bezier_cubic(pya.DPoint(self.Lc/2, 0),pya.DPoint(self.Lc/2, self.r*2),0,pi,a,a,self.accuracy, verbose=True) + \
        p =    bezier_cubic(pya.DPoint(-self.Lc/2, self.r*2), pya.DPoint(-self.Lc/2-self.r/2, self.r*1.5),pi,pi+pi/4,a,0,self.accuracy)
#            bezier_cubic(pya.DPoint(-self.Lc/2, self.r*2), pya.DPoint(-self.Lc/2, 0),pi,pi-pi,a,a,self.accuracy)
        pt1 = translate_from_normal2(p, self.w/2, self.w/2)
        pt2 = translate_from_normal2(p, -self.w/2, -self.w/2)
        pt = pt1 +pt2[::-1]
        wg_polygon = pya.DPolygon(pt)
        cell.shapes(LayerSi).insert(wg_polygon)
        #from SiEPIC.utils.layout import layout_waveguide_uturn_bezier
        #layout_waveguide_uturn_bezier(cell, LayerSi, pya.Trans(pya.Trans.R0, self.Lc/2, 0), w=0.5, h=10.0)
        #layout_waveguide_uturn_bezier(cell, LayerSi, pya.Trans(pya.Trans.R180, -self.Lc/2, self.r*2), w=0.5, h=10.0)

        '''

        # Bends in the racetrack
        y = self.g+self.w
        path = euler_bend(self.r/dbu,self.p)
        turn = 2
        offset = 1
        wg_pts = pya.Path(path, 0).unique_points().get_points()
        width = 0.5e3
        from SiEPIC.utils import translate_from_normal
        wg_polygon = pya.Polygon(translate_from_normal(wg_pts, width/2 + (offset if turn > 0 else - offset)) + translate_from_normal(wg_pts, -width/2 + (offset if turn > 0 else - offset))[::-1])
        cell.shapes(LayerSi).insert(wg_polygon.transformed(pya.Trans(pya.Trans.R0, self.Lc/2/dbu-wg_polygon.bbox().left,y/dbu)))
        cell.shapes(LayerSi).insert(wg_polygon.transformed(pya.Trans(pya.Trans.R180, -self.Lc/2/dbu+wg_polygon.bbox().left,self.r/dbu*2+y/dbu)))

        # straight waveguides in the racetrack
        wg = pya.DBox(-self.Lc/2,-self.w/2+y, self.Lc/2, self.w/2+y)
        cell.shapes(LayerSi).insert(wg)
        cell.shapes(LayerSi).insert(wg.transformed(pya.Trans(pya.Trans.R0,0,self.r*2)))

        # bus waveguide
        wg = pya.DBox(-self.Lc/2-self.r*2,-self.w/2, self.Lc/2+self.r*2, self.w/2)
        cell.shapes(LayerSi).insert(wg)
        

        # Create the pins on the waveguides, as short paths:
        make_pin(self.cell, "opt1", [-self.Lc/2-self.r*2, 0], self.w, LayerPinRecN, 180)
        make_pin(self.cell, "opt2", [self.Lc/2+self.r*2, 0], self.w, LayerPinRecN, 0)

        
        # Create the device recognition layer
        box = pya.DBox(-self.Lc/2-self.r*2,-self.w*3/2, self.Lc/2+self.r*2, y+self.r*2+self.w*2)
        cell.shapes(LayerDevRecN).insert(box)

        '''


        # Compact model information
        t = pya.Trans(pya.Trans.R0, w1 / 10, 0)
        text = Text("Lumerical_INTERCONNECT_library=None", t)
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = pya.Trans(pya.Trans.R0, length / 10, w1 / 4)
        text = pya.Text("Component=racetrack_bezier", t)
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = pya.Trans(pya.Trans.R0, length / 10, w1 / 2)
        text = pya.Text(
            "Spice_param:w=%.3fu g=%.3fu Lc=%.3fu"
            % (self.w, self.g, self.Lc),
            t,
        )
        shape = cell.shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        '''
        
        return (
            "racetrack_euler("
            + ("%.3f-%.3f-%.3f" % (self.w, self.Lc, self.g))
            + ")"
        )


class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("racetrack_euler", racetrack_euler())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: racetrack_euler")

    import siepic_ebeam_pdk
    from SiEPIC.utils.layout import new_layout

    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout for the chip floor plan
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)

    # instantiate the cell
    library = tech + "test_lib"

    # Create for several combinations
    params = [
        {"w": 0.5, "g": 0.1, "Lc": 10, "p": 0.3},
        {"w": 0.5, "g": 0.2, "Lc": 20, "p": 0.8},
    ]
    xmax = 0
    y = 0
    x = xmax
    for p in params:
        print(p)
        pcell = ly.create_cell("racetrack_euler", library, p)
        t = pya.Trans(pya.Trans.R0, x, y - pcell.bbox().bottom)
        inst = topcell.insert(pya.CellInstArray(pcell.cell_index(), t))
        y += pcell.bbox().height() + 2000
        xmax = max(xmax, x + inst.bbox().width())

    # Save
    import os
    from SiEPIC.scripts import export_layout

    path = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.splitext(os.path.basename(__file__))[0]
    file_out = export_layout(topcell, path, filename, format="oas", screenshot=True)

    # Display in KLayout
    from SiEPIC._globals import Python_Env

    if Python_Env == "Script":
        from SiEPIC.utils import klive

        klive.show(file_out, technology=tech, keep_position=True)
