import pya
import math
import cmath
from pya import *
from SiEPIC.utils import get_technology_by_name

MODULE_NUMPY = True

dbu = 0.001
pi = cmath.pi
j = cmath.sqrt(-1)
sign = lambda x: math.copysign(1, x)  # define the sign function
alpha = 1  # related to the spirals radius growth, can only guess and test so far

r = 15.0  # radius of the Sbend spiral
angle_stepsize = 0.0001  # 0.00001 required for less than 1 nm error

# Create aliases for KLayout Python API methods:
Box = pya.Box
Point = pya.Point
Polygon = pya.Polygon
Text = pya.Text
Trans = pya.Trans
LayerInfo = pya.LayerInfo

###################################


# General Spiral Calculation Functions#
def frange(start, stop, step):
    # Used to define a float range, since python doesnt have a built in one
    x = start
    while x < stop:
        yield x  # returns value as generator, speeding up stuff
        x += step


def angle_from_corrugation(r, length, grating_length, gap=8):
    # Calculates the thetas at which the desired grating lengths are achieved. Outputs to an array
    angle = 0
    current_length = 0
    x1 = 0
    y1 = 0
    current_total_length = 0
    yield angle  # yield acts as a return but gives a generator. This early yield is to return the 0 value

    while (
        current_total_length < length + grating_length
    ):  # The spiral gen doesnt draw the last grating because it needs to calculate slope, thus we draw an extra
        while (
            current_length < grating_length
        ):  # if the length has no reached the grating length, continue
            deltaX = (r * sign(angle)) * cmath.exp(-abs(angle) / alpha)
            r_spiral = (r * sign(angle)) + (gap * angle / pi)
            S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
            x2 = S.real
            y2 = S.imag

            angle += angle_stepsize  # continue to increase step size
            current_length = math.sqrt(
                (x2 - x1) ** 2 + (y2 - y1) ** 2
            )  # figureout of the distance betweenthe two points
        # print("currentLength"+str(current_length))
        # print("targetlength"+str(grating_length))
        yield angle
        x1 = S.real
        y1 = S.imag
        current_total_length += current_length
        current_length = 0


def spiral_gen(r, angle_array, w, cwidth, grating_length, gap=8):
    # This generates the spirals coordinates from the given angle arrays. Given there is a cwidth

    for i in frange(0, len(angle_array) - 1, 1):
        angle = angle_array[i]
        angle_next = angle_array[i + 1]

        # Calculate Slope to ensure the gratings are 90 degree with the center guide line, note that the final point will be ignored here and appeneded later
        deltaX = (r * sign(angle_next)) * cmath.exp(
            -abs(angle_next) / alpha
        )  # r, not r_inc here because then it will all end at 0,0
        # Second Point
        r_spiral = (r * sign(angle_next)) + (gap * angle_next / pi)
        S = (r_spiral * cmath.exp(j * abs(angle_next))) - deltaX
        x2 = S.real
        y2 = S.imag
        deltaX = (r * sign(angle)) * cmath.exp(
            -abs(angle) / alpha
        )  # r, not r_inc here because then it will all end at 0,0
        # First Point
        r_spiral = (r * sign(angle)) + (gap * angle / pi)
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        x1 = S.real
        y1 = S.imag
        # Slope
        if grating_length != 0:
            dx = (x2 - x1) / grating_length
            dy = (y2 - y1) / grating_length
        else:
            print("Grating_Length is 0, use legacy function")

        # Calculate the Coordinate for each grating and apply the slope modifer
        # Outer, C1
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc1 = S.real + dy * (w + cwidth)
        ycoor_Winc1 = S.imag - dx * (w + cwidth)
        # Outer C2
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc2 = S.real + dy * (w - cwidth)
        ycoor_Winc2 = S.imag - dx * (w - cwidth)
        # Inner, C1
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc3 = S.real - dy * (w - cwidth)
        ycoor_Winc3 = S.imag + dx * (w - cwidth)
        # Inner C2

        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc4 = S.real - dy * (w + cwidth)
        ycoor_Winc4 = S.imag + dx * (w + cwidth)

        if cwidth != 0:
            yield (
                xcoor_Winc1,
                ycoor_Winc1,
                xcoor_Winc2,
                ycoor_Winc2,
                xcoor_Winc3,
                ycoor_Winc3,
                xcoor_Winc4,
                ycoor_Winc4,
                dx,
                dy,
            )
        else:
            yield xcoor_Winc1, ycoor_Winc1, xcoor_Winc3, ycoor_Winc3, dx, dy


def sort_coord(bool_order, xinc, yinc, xdec, ydec):
    # this organizes the two sets of coordinates for each wall into an order to create gratings
    # can pass bool_order to decide which gets drawn first
    x_array = []
    y_array = []

    for i in range(len(xinc)):
        if bool_order == True:
            x_array.append(xdec[i])
            x_array.append(xinc[i])
            y_array.append(ydec[i])
            y_array.append(yinc[i])
            bool_order = not bool_order
        else:
            x_array.append(xinc[i])
            x_array.append(xdec[i])
            y_array.append(yinc[i])
            y_array.append(ydec[i])
            bool_order = not bool_order
    return x_array, y_array


def finish_spiral(r, finalangle, w, dx, dy, gap=8):
    # This finishes the spiral to the 0 or 180 position with a uniform waveguide, also makes it easier to match via pins
    # The radius of the individual walls, basically draws 2 lines for each wall of the waveguide and appends hte points
    r_Winc = r + w
    r_Wdec = r - w

    x_inc = []
    y_inc = []
    x_dec = []
    y_dec = []

    deltaX = (r * sign(finalangle)) * cmath.exp(-abs(finalangle) / alpha)
    r_spiral = (r * sign(finalangle)) + (gap * finalangle / pi)
    S = (r_spiral * cmath.exp(j * abs(finalangle))) - deltaX
    x_inc.append(S.real + dy * w)
    y_inc.append(S.imag - dx * w)

    r_spiral = (r * sign(finalangle)) + (gap * finalangle / pi)
    S = (r_spiral * cmath.exp(j * abs(finalangle))) - deltaX
    x_dec.append(S.real - dy * w)
    y_dec.append(S.imag + dx * w)

    nextpie = math.ceil(finalangle / (pi)) * pi
    for angle in frange(finalangle + 0.01, nextpie, 0.01):
        deltaX = (r * sign(angle)) * cmath.exp(-abs(angle) / alpha)

        r_spiral = (r_Winc * sign(angle)) + (gap * angle / pi)
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        x_inc.append(S.real)
        y_inc.append(S.imag)

        r_spiral = (r_Wdec * sign(angle)) + (gap * angle / pi)
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        x_dec.append(S.real)
        y_dec.append(S.imag)

    # appends the final coordinate at y=0
    deltaX = (r * sign(nextpie)) * cmath.exp(-abs(nextpie) / alpha)
    r_spiral = (r_Winc * sign(nextpie)) + (gap * nextpie / pi)
    S = (r_spiral * cmath.exp(j * abs(nextpie))) - deltaX
    x_inc.append(S.real)
    y_inc.append(S.imag)

    deltaX = (r * sign(nextpie)) * cmath.exp(-abs(nextpie) / alpha)
    r_spiral = (r_Wdec * sign(nextpie)) + (gap * nextpie / pi)
    S = (r_spiral * cmath.exp(j * abs(nextpie))) - deltaX
    x_dec.append(S.real)
    y_dec.append(S.imag)

    # deltaX = (r*sign(nextpie))*cmath.exp(-abs(nextpie)/alpha)
    # r_spiral = (r*sign(nextpie))+(gap*nextpie/pi)
    # S = (r_spiral*cmath.exp(j*abs(nextpie)))-deltaX
    # endx = S.real

    # if math.ceil(nextpie/pi) %2 ==0:
    # isEven = True
    # print ("even")
    # print (nextpie)
    # print (math.ceil(nextpie/pi) %2)
    # else:
    # isEven = False
    # print ("odd")
    # print (nextpie)
    # print (math.ceil(nextpie/pi) %2)

    return x_inc, y_inc, x_dec, y_dec  # ,endx,isEven


def spiral_gen_NoCenter(r, angle_array, w, cwidth, grating_length, gap=8):
    # This generates the spirals coordinates from the given angle arrays. Given there is a cwidth
    # for i in frange(0,len(angle_array)-1,1):
    i = 0
    angle = 0
    xc1 = []
    xc2 = []
    yc1 = []
    yc2 = []

    while angle < pi:
        angle = angle_array[i]
        angle_next = angle_array[i + 1]

        # Calculate Slope to ensure the gratings are 90 degree with the center guide line, note that the final point will be ignored here and appeneded later
        deltaX = (r * sign(angle_next)) * cmath.exp(
            -abs(angle_next) / alpha
        )  # r, not r_inc here because then it will all end at 0,0
        # Second Point
        r_spiral = (r * sign(angle_next)) + (gap * angle_next / pi)
        S = (r_spiral * cmath.exp(j * abs(angle_next))) - deltaX
        x2 = S.real
        y2 = S.imag
        deltaX = (r * sign(angle)) * cmath.exp(
            -abs(angle) / alpha
        )  # r, not r_inc here because then it will all end at 0,0
        # First Point
        r_spiral = (r * sign(angle)) + (gap * angle / pi)
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        x1 = S.real
        y1 = S.imag
        # Slope
        if grating_length != 0:
            dx = (x2 - x1) / grating_length
            dy = (y2 - y1) / grating_length
        else:
            print("Grating_Length is 0, use legacy function")
        # Calculate the Coordinate for each grating and apply the slope modifer
        # Outer, C1
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xc1.append(S.real + dy * (w))
        yc1.append(S.imag - dx * (w))
        # Inner, C1
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xc2.append(S.real - dy * (w))
        yc2.append(S.imag + dx * (w))
        i += 1

    return xc1, yc1, xc2, yc2, i


def spiral_gen_NoCenter_Gratings(
    r, angle_array, w, cwidth, grating_length, lasti, gap=8
):
    # This generates the spirals coordinates from the given angle arrays. Given there is a cwidth

    for i in frange(lasti, len(angle_array) - 1, 1):
        angle = angle_array[i]
        angle_next = angle_array[i + 1]

        # Calculate Slope to ensure the gratings are 90 degree with the center guide line, note that the final point will be ignored here and appeneded later
        deltaX = (r * sign(angle_next)) * cmath.exp(
            -abs(angle_next) / alpha
        )  # r, not r_inc here because then it will all end at 0,0
        # Second Point
        r_spiral = (r * sign(angle_next)) + (gap * angle_next / pi)
        S = (r_spiral * cmath.exp(j * abs(angle_next))) - deltaX
        x2 = S.real
        y2 = S.imag
        deltaX = (r * sign(angle)) * cmath.exp(
            -abs(angle) / alpha
        )  # r, not r_inc here because then it will all end at 0,0
        # First Point
        r_spiral = (r * sign(angle)) + (gap * angle / pi)
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        x1 = S.real
        y1 = S.imag
        # Slope
        if grating_length != 0:
            dx = (x2 - x1) / grating_length
            dy = (y2 - y1) / grating_length
        else:
            print("Grating_Length is 0, use legacy function")

        # Calculate the Coordinate for each grating and apply the slope modifer
        # Outer, C1
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc1 = S.real + dy * (w + cwidth)
        ycoor_Winc1 = S.imag - dx * (w + cwidth)
        # Outer C2
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc2 = S.real + dy * (w - cwidth)
        ycoor_Winc2 = S.imag - dx * (w - cwidth)
        # Inner, C1
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc3 = S.real - dy * (w - cwidth)
        ycoor_Winc3 = S.imag + dx * (w - cwidth)
        # Inner C2

        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc4 = S.real - dy * (w + cwidth)
        ycoor_Winc4 = S.imag + dx * (w + cwidth)

        if cwidth != 0:
            yield (
                xcoor_Winc1,
                ycoor_Winc1,
                xcoor_Winc2,
                ycoor_Winc2,
                xcoor_Winc3,
                ycoor_Winc3,
                xcoor_Winc4,
                ycoor_Winc4,
                dx,
                dy,
            )
        else:
            yield xcoor_Winc1, ycoor_Winc1, xcoor_Winc3, ycoor_Winc3, dx, dy


def angle_from_corrugation_NoCenter(r, length, grating_length, gap=8):
    # Calculates the thetas at which the desired grating lengths are achieved. Outputs to an array
    angle = 0
    current_length = 0
    x1 = 0
    y1 = 0
    current_total_length = 0

    ##
    length *= 2  # length needs to be double since all gratings on one side
    ##

    yield angle  # yield acts as a return but gives a generator. This early yield is to return the 0 value

    while (
        current_total_length < length + grating_length
    ):  # The spiral gen doesnt draw the last grating because it needs to calculate slope, thus we draw an extra
        while (
            current_length < grating_length
        ):  # if the length has no reached the grating length, continue
            deltaX = (r * sign(angle)) * cmath.exp(-abs(angle) / alpha)
            r_spiral = (r * sign(angle)) + (gap * angle / pi)
            S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
            x2 = S.real
            y2 = S.imag

            angle += angle_stepsize  # continue to increase step size
            current_length = math.sqrt(
                (x2 - x1) ** 2 + (y2 - y1) ** 2
            )  # figureout of the distance betweenthe two points
        # print("currentLength"+str(current_length))
        # print("targetlength"+str(grating_length))
        yield angle
        x1 = S.real
        y1 = S.imag
        if angle > pi:
            current_total_length += current_length
        current_length = 0


def CDC_gen(
    r, angle_array, w, w2, cwidth, cwidth2, grating_length, wgap, direction, gap=8
):
    # This generates the spirals coordinates from the given angle arrays. Given there is a cwidth
    # iangle_array = [i*-1 for i in angle_array]
    # angle_array = angle_array[::-1]
    # angle_array.extend(iangle_array)
    for i in frange(0, len(angle_array) - 1, 1):
        angle = angle_array[i]
        angle_next = angle_array[i + 1]
        # Calculate Slope to ensure the gratings are 90 degree with the center guide line, note that the final point will be ignored here and appeneded later
        deltaX = (r * sign(angle_next)) * cmath.exp(
            -abs(angle_next) / alpha
        )  # r, not r_inc here because then it will all end at 0,0
        # Second Point
        r_spiral = (r * sign(angle_next)) + (gap * angle_next / pi)
        S = ((r_spiral) * cmath.exp(j * abs(angle_next))) - deltaX
        x2 = S.real
        y2 = S.imag
        deltaX = (r * sign(angle)) * cmath.exp(
            -abs(angle) / alpha
        )  # r, not r_inc here because then it will all end at 0,0
        # First Point
        r_spiral = (r * sign(angle)) + (gap * angle / pi)
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        x1 = S.real
        y1 = S.imag
        # Slope
        if grating_length != 0:
            dx = (x2 - x1) / grating_length
            dy = (y2 - y1) / grating_length
        else:
            print("Grating_Length is 0, use legacy function")

        # Calculate the Coordinate for each grating and apply the slope modifer
        # WG1
        # Outer, C1
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc1 = S.real + dy * (w - direction * cwidth + wgap + w + cwidth)
        ycoor_Winc1 = S.imag - dx * (w - direction * cwidth + wgap + w + cwidth)
        # Outer C2
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc2 = S.real + dy * (w + direction * cwidth + wgap + w + cwidth)
        ycoor_Winc2 = S.imag - dx * (w + direction * cwidth + wgap + w + cwidth)
        # Inner, C1
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc3 = S.real - dy * (w - direction * cwidth - wgap - w - cwidth)
        ycoor_Winc3 = S.imag + dx * (w - direction * cwidth - wgap - w - cwidth)
        # Inner C2
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        xcoor_Winc4 = S.real - dy * (w + direction * cwidth - wgap - w - cwidth)
        ycoor_Winc4 = S.imag + dx * (w + direction * cwidth - wgap - w - cwidth)

        # wG2
        # Outer, C1
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        w2xcoor_Winc1 = S.real + dy * (w2 + direction * cwidth2 - wgap - w2 - cwidth2)
        w2ycoor_Winc1 = S.imag - dx * (w2 + direction * cwidth2 - wgap - w2 - cwidth2)
        # Outer C2
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        w2xcoor_Winc2 = S.real + dy * (w2 - direction * cwidth2 - wgap - w2 - cwidth2)
        w2ycoor_Winc2 = S.imag - dx * (w2 - direction * cwidth2 - wgap - w2 - cwidth2)
        # Inner, C1
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        w2xcoor_Winc3 = S.real - dy * (w2 + direction * cwidth2 + wgap + w2 + cwidth2)
        w2ycoor_Winc3 = S.imag + dx * (w2 + direction * cwidth2 + wgap + w2 + cwidth2)
        # Inner C2
        S = ((r_spiral) * cmath.exp(j * abs(angle))) - deltaX
        w2xcoor_Winc4 = S.real - dy * (w2 - direction * cwidth2 + wgap + w2 + cwidth2)
        w2ycoor_Winc4 = S.imag + dx * (w2 - direction * cwidth2 + wgap + w2 + cwidth2)

        if cwidth != 0:
            yield (
                xcoor_Winc1,
                ycoor_Winc1,
                xcoor_Winc2,
                ycoor_Winc2,
                xcoor_Winc3,
                ycoor_Winc3,
                xcoor_Winc4,
                ycoor_Winc4,
                dx,
                dy,
                w2xcoor_Winc1,
                w2ycoor_Winc1,
                w2xcoor_Winc2,
                w2ycoor_Winc2,
                w2xcoor_Winc3,
                w2ycoor_Winc3,
                w2xcoor_Winc4,
                w2ycoor_Winc4,
            )
        else:
            yield (
                xcoor_Winc1,
                ycoor_Winc1,
                xcoor_Winc3,
                ycoor_Winc3,
                dx,
                dy,
                w2xcoor_Winc1,
                w2ycoor_Winc1,
                w2xcoor_Winc3,
                w2ycoor_Winc3,
            )


def finish_CDC(r, finalangle, w, dx, dy, cwidth, wgap, direction, gap=8):
    # This finishes the spiral to the 0 or 180 position with a uniform waveguide, also makes it easier to match via pins
    # The radius of the individual walls, basically draws 2 lines for each wall of the waveguide and appends hte points
    r_Winc = r + w + direction * (cwidth + wgap + w)
    r_Wdec = r - w + direction * (cwidth + wgap + w)

    x_inc = []
    y_inc = []
    x_dec = []
    y_dec = []

    deltaX = (r * sign(finalangle)) * cmath.exp(-abs(finalangle) / alpha)
    r_spiral = ((r) * sign(finalangle)) + (gap * finalangle / pi)
    S = (r_spiral * cmath.exp(j * abs(finalangle))) - deltaX
    x_inc.append(S.real + dy * w + dy * direction * (wgap + w + cwidth))
    y_inc.append(S.imag - dx * w - dx * direction * (wgap + w + cwidth))

    r_spiral = ((r) * sign(finalangle)) + (gap * finalangle / pi)
    S = (r_spiral * cmath.exp(j * abs(finalangle))) - deltaX
    x_dec.append(S.real - dy * w - dy * direction * (-wgap - w - cwidth))
    y_dec.append(S.imag + dx * w + dx * direction * (-wgap - w - cwidth))

    nextpie = math.ceil(finalangle / (pi)) * pi
    for angle in frange(finalangle + 0.01, nextpie, 0.01):
        deltaX = (r * sign(angle)) * cmath.exp(-abs(angle) / alpha)

        r_spiral = (r_Winc * sign(angle)) + (gap * angle / pi)
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        x_inc.append(S.real)
        y_inc.append(S.imag)

        r_spiral = (r_Wdec * sign(angle)) + (gap * angle / pi)
        S = (r_spiral * cmath.exp(j * abs(angle))) - deltaX
        x_dec.append(S.real)
        y_dec.append(S.imag)

    # appends the final coordinate at y=0
    deltaX = (r * sign(nextpie)) * cmath.exp(-abs(nextpie) / alpha)
    r_spiral = (r_Winc * sign(nextpie)) + (gap * nextpie / pi)
    S = (r_spiral * cmath.exp(j * abs(nextpie))) - deltaX
    x_inc.append(S.real)
    y_inc.append(S.imag)
    endx1 = S.real

    deltaX = (r * sign(nextpie)) * cmath.exp(-abs(nextpie) / alpha)
    r_spiral = (r_Wdec * sign(nextpie)) + (gap * nextpie / pi)
    S = (r_spiral * cmath.exp(j * abs(nextpie))) - deltaX
    x_dec.append(S.real)
    y_dec.append(S.imag)
    endx2 = S.real

    return x_inc, y_inc, x_dec, y_dec, endx1, endx2


###########################


class PCMSpiralBraggGrating(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(PCMSpiralBraggGrating, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("w", self.TypeDouble, "Waveguide Width [nm]", default=400)
        self.param(
            "DeviceLength", self.TypeDouble, "Device Path Length [mm]", default=0.5
        )
        self.param("Cwidth", self.TypeDouble, "Corrugation Width [nm]", default=80)
        self.param("period", self.TypeDouble, "period [nm]", default=420)
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "SpiralBraggGrating"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        from SiEPIC._globals import PIN_LENGTH
        # This is the main part of the implementation: create the layout

        # fetch the parameters
        # self.w = 400
        # self.Length = 0.5
        # self.Cwidth = 80
        # self.pitch = 420
        # self.Chirp_Rate = 0
        # self.n = 1800

        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSiN = ly.layer(LayerSi)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)

        w = self.w * 10**-3 / 2.0  # drawing from center line, only have to add half
        length = self.DeviceLength * 1000 / 2.0  # only drawing half and then copying
        cwidth = self.Cwidth * 10**-3 / 2.0  # same reason as width
        grating_length = self.period / 2.0 * 10**-3

        # Step1 Find the Angles of each grating#######
        angle_array = []
        for theta in angle_from_corrugation(r, length, grating_length):
            angle_array.append(theta)
        ####################

        #####################
        # Step2 Find the Coordinates of the gratings via the angles
        # Wall1 of the Left
        left_x_inc = []
        left_y_inc = []
        left_x_dec = []
        left_y_dec = []
        # Wall2 of the Left
        left2_x_inc = []
        left2_y_inc = []
        left2_x_dec = []
        left2_y_dec = []

        # Calculate the Spiral Coordinates
        for coord in spiral_gen(r, angle_array, w, cwidth, grating_length):
            left_x_inc.append(coord[0])
            left_y_inc.append(coord[1])
            left_x_dec.append(coord[2])
            left_y_dec.append(coord[3])

            left2_x_inc.append(coord[4])
            left2_y_inc.append(coord[5])
            left2_x_dec.append(coord[6])
            left2_y_dec.append(coord[7])
        dx = coord[8]
        dy = coord[9]
        # Flip coords for right side coords
        right_x_inc = [i * -1 for i in left_x_inc]
        right_y_inc = [i * -1 for i in left_y_inc]
        right_x_dec = [i * -1 for i in left_x_dec]
        right_y_dec = [i * -1 for i in left_y_dec]

        right2_x_inc = [i * -1 for i in left2_x_inc]
        right2_y_inc = [i * -1 for i in left2_y_inc]
        right2_x_dec = [i * -1 for i in left2_x_dec]
        right2_y_dec = [i * -1 for i in left2_y_dec]
        # Obtain a sorted list of the coordinates of one wall.
        # repeat for the rest
        result = sort_coord(True, left_x_inc, left_y_inc, left_x_dec, left_y_dec)
        left1x = result[0]
        left1y = result[1]
        result = sort_coord(False, left2_x_inc, left2_y_inc, left2_x_dec, left2_y_dec)
        left2x = result[0]
        left2y = result[1]

        result = sort_coord(False, right_x_inc, right_y_inc, right_x_dec, right_y_dec)
        right1x = result[0]
        right1y = result[1]

        # Delete the first two points as they over lap
        del right1x[
            0
        ]  # calls the same index here because once you remove 0, 1 becomes 0, and so on and so forth
        del right1x[0]
        del right1y[0]
        del right1y[0]

        result = sort_coord(
            True, right2_x_inc, right2_y_inc, right2_x_dec, right2_y_dec
        )
        right2x = result[0]
        right2y = result[1]
        del right2x[0]
        del right2x[0]
        del right2y[0]
        del right2y[0]

        # UNIFORM SECTION

        del left1x[-1]
        del left1y[-1]
        del left2x[-1]
        del left2y[-1]

        del right1x[-1]
        del right1y[-1]
        del right2x[-1]
        del right2y[-1]

        result = finish_spiral(r, angle_array[-2], w, dx, dy)
        left1x.extend(result[0])
        left1y.extend(result[1])
        left2x.extend(result[2])
        left2y.extend(result[3])

        right1x.extend(i * -1 for i in result[0])
        right1y.extend(i * -1 for i in result[1])
        right2x.extend(i * -1 for i in result[2])
        right2y.extend(i * -1 for i in result[3])
        #########################################

        # Step3 Organize all the points into a single matrix to be drawn in klayout.
        spiral_x = []
        spiral_y = []

        spiral_x.extend(reversed(left1x))
        spiral_x.extend(right2x)
        spiral_x.extend(reversed(right1x))
        spiral_x.extend(left2x)

        spiral_y.extend(reversed(left1y))
        spiral_y.extend(right2y)
        spiral_y.extend(reversed(right1y))
        spiral_y.extend(left2y)

        # makes Dpoints from the coordinates
        dpts = [pya.DPoint(spiral_x[i], spiral_y[i]) for i in range(len(spiral_x))]
        dpolygon = DPolygon(dpts)
        # dmult_pts = mult_pts(dpts,1)

        # dpoint polygon solution thanks to Jaspreet#
        element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
        shapes(LayerSiN).insert(element)
        # shapes(LayerSiN).insert(Polygon.from_dpoly(dpolygon))

        # Create the pins, as short paths:
        DeviceHeight = self.cell.bbox().height()

        # WG1
        wg1 = Box(
            self.cell.bbox().width() / 2.0,
            0,
            self.cell.bbox().width() / 2.0 - 2 * w / dbu,
            DeviceHeight / 2.0,
        )
        shapes(LayerSiN).insert(wg1)
        # WG2
        wg2 = Box(
            -self.cell.bbox().width() / 2.0,
            0,
            -self.cell.bbox().width() / 2.0 + 2 * w / dbu,
            -DeviceHeight / 2.0,
        )
        shapes(LayerSiN).insert(wg2)

        # pin1
        pin = pya.Path(
            [
                Point(
                    -(self.cell.bbox().width() / 2.0) + w / dbu,
                    -DeviceHeight / 2.0 + PIN_LENGTH / 2.0,
                ),
                Point(
                    -(self.cell.bbox().width() / 2.0) + w / dbu,
                    -DeviceHeight / 2.0 - PIN_LENGTH / 2.0,
                ),
            ],
            w / dbu * 2.0,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(
            Trans.R0, -(self.cell.bbox().width() / 2.0) + w / dbu, -DeviceHeight / 2.0
        )
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        # pin2
        pin = pya.Path(
            [
                Point(
                    (self.cell.bbox().width() / 2.0) - w / dbu,
                    DeviceHeight / 2.0 - PIN_LENGTH / 2.0,
                ),
                Point(
                    (self.cell.bbox().width() / 2.0) - w / dbu,
                    DeviceHeight / 2.0 + PIN_LENGTH / 2.0,
                ),
            ],
            w / dbu * 2.0,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(
            Trans.R0, (self.cell.bbox().width() / 2.0) - w / dbu, DeviceHeight / 2.0
        )
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer
        # I literally declared the size of this box based on the other box. Lol.
        dev = Box(
            -self.cell.bbox().width() / 2.0,
            -self.cell.bbox().height() / 2.0 + PIN_LENGTH / 2.0,
            self.cell.bbox().width() / 2.0,
            self.cell.bbox().height() / 2.0 - PIN_LENGTH / 2.0,
        )
        shapes(LayerDevRecN).insert(dev)

        print("Done drawing the layout for - PCM Spiral")


class PCMSpiralBraggGratingSlab(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(PCMSpiralBraggGratingSlab, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("w", self.TypeDouble, "Waveguide Width [nm]", default=400)
        self.param(
            "DeviceLength", self.TypeDouble, "Device Path Length [mm]", default=0.5
        )
        self.param("Cwidth", self.TypeDouble, "Corrugation Width [nm]", default=80)
        self.param("period", self.TypeDouble, "period [nm]", default=420)
        self.param(
            "silayer2", self.TypeLayer, "Slab Si Layer", default=LayerInfo(31, 0)
        )
        self.param("sw", self.TypeDouble, "Slab Width [nm]", default=500)
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "SpiralBraggGratingSlab"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        from SiEPIC._globals import PIN_LENGTH

        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSiN = ly.layer(LayerSi)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)
        LayerSiN_Slab = ly.layer(self.silayer2)

        w = self.w * 10**-3 / 2.0  # drawing from center line, only have to add half
        length = self.DeviceLength * 1000 / 2.0  # only drawing half and then copying
        cwidth = self.Cwidth * 10**-3 / 2.0  # same reason as width
        grating_length = self.period / 2.0 * 10**-3
        sw = self.sw * 10**-3 / 2.0

        # Step1 Find the Angles of each grating#######
        angle_array = []
        for theta in angle_from_corrugation(r, length, grating_length):
            angle_array.append(theta)
        ####################

        #####################
        # Step2 Find the Coordinates of the gratings via the angles
        # Wall1 of the Left
        left_x_inc = []
        left_y_inc = []
        left_x_dec = []
        left_y_dec = []
        # Wall2 of the Left
        left2_x_inc = []
        left2_y_inc = []
        left2_x_dec = []
        left2_y_dec = []

        # Calculate the Spiral Coordinates
        for coord in spiral_gen(r, angle_array, w, cwidth, grating_length):
            left_x_inc.append(coord[0])
            left_y_inc.append(coord[1])
            left_x_dec.append(coord[2])
            left_y_dec.append(coord[3])

            left2_x_inc.append(coord[4])
            left2_y_inc.append(coord[5])
            left2_x_dec.append(coord[6])
            left2_y_dec.append(coord[7])
        dx = coord[8]
        dy = coord[9]
        # Flip coords for right side coords
        right_x_inc = [i * -1 for i in left_x_inc]
        right_y_inc = [i * -1 for i in left_y_inc]
        right_x_dec = [i * -1 for i in left_x_dec]
        right_y_dec = [i * -1 for i in left_y_dec]

        right2_x_inc = [i * -1 for i in left2_x_inc]
        right2_y_inc = [i * -1 for i in left2_y_inc]
        right2_x_dec = [i * -1 for i in left2_x_dec]
        right2_y_dec = [i * -1 for i in left2_y_dec]
        # Obtain a sorted list of the coordinates of one wall.
        # repeat for the rest
        result = sort_coord(True, left_x_inc, left_y_inc, left_x_dec, left_y_dec)
        left1x = result[0]
        left1y = result[1]
        result = sort_coord(False, left2_x_inc, left2_y_inc, left2_x_dec, left2_y_dec)
        left2x = result[0]
        left2y = result[1]

        result = sort_coord(False, right_x_inc, right_y_inc, right_x_dec, right_y_dec)
        right1x = result[0]
        right1y = result[1]
        # Delete the first two points as they over lap
        del right1x[
            0
        ]  # calls the same index here because once you remove 0, 1 becomes 0, and so on and so forth
        del right1x[0]
        del right1y[0]
        del right1y[0]

        result = sort_coord(
            True, right2_x_inc, right2_y_inc, right2_x_dec, right2_y_dec
        )
        right2x = result[0]
        right2y = result[1]
        del right2x[0]
        del right2x[0]
        del right2y[0]
        del right2y[0]

        # UNIFORM SECTION

        del left1x[-1]
        del left1y[-1]
        del left2x[-1]
        del left2y[-1]

        del right1x[-1]
        del right1y[-1]
        del right2x[-1]
        del right2y[-1]

        result = finish_spiral(r, angle_array[-2], w, dx, dy)
        left1x.extend(result[0])
        left1y.extend(result[1])
        left2x.extend(result[2])
        left2y.extend(result[3])

        right1x.extend(i * -1 for i in result[0])
        right1y.extend(i * -1 for i in result[1])
        right2x.extend(i * -1 for i in result[2])
        right2y.extend(i * -1 for i in result[3])
        #########################################

        # Step3 Organize all the points into a single matrix to be drawn in klayout.
        spiral_x = []
        spiral_y = []

        spiral_x.extend(reversed(left1x))
        spiral_x.extend(right2x)
        spiral_x.extend(reversed(right1x))
        spiral_x.extend(left2x)

        spiral_y.extend(reversed(left1y))
        spiral_y.extend(right2y)
        spiral_y.extend(reversed(right1y))
        spiral_y.extend(left2y)

        # makes Dpoints from the coordinates
        dpts = [pya.DPoint(spiral_x[i], spiral_y[i]) for i in range(len(spiral_x))]
        dpolygon = DPolygon(dpts)
        # dmult_pts = mult_pts(dpts,1)

        # dpoint polygon solution thanks to Jaspreet#
        element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
        shapes(LayerSiN).insert(element)

        # Step4 Draw slab spiral
        # Step2 Find the Coordinates of the gratings via the angles
        # Wall1 of the Left
        left_xS = []
        left_yS = []
        # Wall2 of the Left
        left2_xS = []
        left2_yS = []

        # Calculate the Spiral Coordinates
        for coord in spiral_gen(r, angle_array, sw, 0, grating_length):
            # for coord in spiral_gen_legacy(r,angle_array,sw):
            left_xS.append(coord[0])
            left_yS.append(coord[1])
            left2_xS.append(coord[2])
            left2_yS.append(coord[3])
        dx = coord[4]
        dy = coord[5]
        # Flip coords for right side coords
        right_xS = [i * -1 for i in left_xS]
        right_yS = [i * -1 for i in left_yS]
        right2_xS = [i * -1 for i in left2_xS]
        right2_yS = [i * -1 for i in left2_yS]
        # Obtain a sorted list of the coordinates of one wall.

        # Delete the first two points as they over lap
        del right_xS[
            0
        ]  # calls the same index here because once you remove 0, 1 becomes 0, and so on and so forth
        del right_xS[0]
        del right_yS[0]
        del right_yS[0]

        del right2_xS[0]
        del right2_xS[0]
        del right2_yS[0]
        del right2_yS[0]

        # UNIFORM SECTION
        del left_xS[-1]
        del left_yS[-1]
        del left2_xS[-1]
        del left2_yS[-1]

        del right_xS[-1]
        del right_yS[-1]
        del right2_xS[-1]
        del right2_yS[-1]

        result = finish_spiral(r, angle_array[-1], sw, dx, dy)
        left_xS.extend(result[0])
        left_yS.extend(result[1])
        left2_xS.extend(result[2])
        left2_yS.extend(result[3])

        right_xS.extend(i * -1 for i in result[0])
        right_yS.extend(i * -1 for i in result[1])
        right2_xS.extend(i * -1 for i in result[2])
        right2_yS.extend(i * -1 for i in result[3])
        #########################################

        # Step4.5 Organize all the points into a single matrix to be drawn in klayout.
        slab_x = []
        slab_y = []

        slab_x.extend(reversed(left_xS))
        slab_x.extend(right2_xS)
        slab_x.extend(reversed(right_xS))
        slab_x.extend(left2_xS)

        slab_y.extend(reversed(left_yS))
        slab_y.extend(right2_yS)
        slab_y.extend(reversed(right_yS))
        slab_y.extend(left2_yS)

        # makes Dpoints from the coordinates
        dptsS = [pya.DPoint(slab_x[i], slab_y[i]) for i in range(len(slab_x))]
        dpolygonS = DPolygon(dptsS)
        # dmult_pts = mult_pts(dpts,1)

        # Step6 Pins!
        DeviceWidthNS = (
            self.cell.bbox().width()
        )  # width of device without slab included yet, for drawing WG

        # insert slab
        # dpoint polygon solution thanks to Jaspreet#
        elementS = Polygon.from_dpoly(dpolygonS * (1.0 / dbu))
        shapes(LayerSiN_Slab).insert(elementS)
        # Slab Tapers
        dpts = [
            pya.DPoint(-(self.cell.bbox().width() / 2.0 * dbu), 0),
            pya.DPoint(-(self.cell.bbox().width() / 2.0) * dbu + sw * 2.0, 0),
            pya.DPoint(
                -(self.cell.bbox().width() / 2.0) * dbu + (sw - w) + w * 2.0, -10
            ),
            pya.DPoint(-(self.cell.bbox().width() / 2.0) * dbu + (sw - w), -10),
        ]
        dpolygon = DPolygon(dpts)
        element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
        shapes(LayerSiN_Slab).insert(element)
        dpts = [
            pya.DPoint((self.cell.bbox().width() / 2.0 * dbu), 0),
            pya.DPoint((self.cell.bbox().width() / 2.0) * dbu - sw * 2.0, 0),
            pya.DPoint(
                (self.cell.bbox().width() / 2.0) * dbu - (sw - w) - w * 2.0, +10
            ),
            pya.DPoint((self.cell.bbox().width() / 2.0) * dbu - (sw - w), +10),
        ]
        dpolygon = DPolygon(dpts)
        element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
        shapes(LayerSiN_Slab).insert(element)

        DeviceHeight = self.cell.bbox().height() * dbu

        # WG1
        wg1 = Box(
            DeviceWidthNS / 2.0,
            0,
            DeviceWidthNS / 2.0 - 2 * w / dbu,
            DeviceHeight / dbu / 2.0,
        )
        shapes(LayerSiN).insert(wg1)
        # WG2
        wg2 = Box(
            -DeviceWidthNS / 2.0,
            0,
            -DeviceWidthNS / 2.0 + 2 * w / dbu,
            -DeviceHeight / dbu / 2.0,
        )
        shapes(LayerSiN).insert(wg2)

        # Pin1
        pin = pya.Path(
            [
                Point(
                    (-DeviceWidthNS / 2.0) + w / dbu,
                    -DeviceHeight / 2.0 / dbu + PIN_LENGTH / 2.0,
                ),
                Point(
                    (-DeviceWidthNS / 2.0) + w / dbu,
                    -DeviceHeight / 2.0 / dbu - PIN_LENGTH / 2.0,
                ),
            ],
            w / dbu * 2.0,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, -(DeviceWidthNS / 2.0) + w / dbu, -DeviceHeight / 2.0 / dbu)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        # Pin2
        pin = pya.Path(
            [
                Point(
                    (DeviceWidthNS / 2.0) - w / dbu,
                    DeviceHeight / 2.0 / dbu - PIN_LENGTH / 2.0,
                ),
                Point(
                    (DeviceWidthNS / 2.0) - w / dbu,
                    DeviceHeight / 2.0 / dbu + PIN_LENGTH / 2.0,
                ),
            ],
            w / dbu * 2.0,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, (DeviceWidthNS / 2.0) - w / dbu, DeviceHeight / 2.0 / dbu)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer
        # I literally declared the size of this box based on the other box. Lol.
        dev = Box(
            -self.cell.bbox().width() / 2.0,
            -self.cell.bbox().height() / 2.0 + PIN_LENGTH / 2.0,
            self.cell.bbox().width() / 2.0,
            self.cell.bbox().height() / 2.0 - PIN_LENGTH / 2.0,
        )
        shapes(LayerDevRecN).insert(dev)

        print("Done drawing the layout for - PCM Spiral with Slabs")


class Spiral_NoCenterBraggGrating(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(Spiral_NoCenterBraggGrating, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("w", self.TypeDouble, "Waveguide Width [nm]", default=400)
        self.param(
            "DeviceLength", self.TypeDouble, "Device Path Length [mm]", default=0.5
        )
        self.param("Cwidth", self.TypeDouble, "Corrugation Width [nm]", default=80)
        self.param("period", self.TypeDouble, "period [nm]", default=420)
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "SpiralBraggGrating"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout
        from SiEPIC._globals import PIN_LENGTH

        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSiN = ly.layer(LayerSi)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)

        w = self.w * 10**-3 / 2.0  # drawing from center line, only have to add half
        length = self.DeviceLength * 1000 / 2.0  # only drawing half and then copying
        cwidth = self.Cwidth * 10**-3 / 2.0  # same reason as width
        grating_length = self.period / 2.0 * 10**-3

        # Step1 Find the Angles of each grating#######
        angle_array = []
        for theta in angle_from_corrugation(r, length, grating_length):
            angle_array.append(theta)

        # IF WANT TO CALCULATE BASED ON LENGTH OF WG that includes gratings
        """    
    angle_array_NoCenter=[]
    for theta in angle_from_corrugation_NoCenter(r,length,grating_length):
        angle_array_NoCenter.append(theta)
    """
        ####################

        #####################
        # Step2 Find the Coordinates of the gratings via the angles
        # Wall1 of the Left
        left_x_inc = []
        left_y_inc = []
        left_x_dec = []
        left_y_dec = []
        # Wall2 of the Left
        left2_x_inc = []
        left2_y_inc = []
        left2_x_dec = []
        left2_y_dec = []

        nongrating = spiral_gen_NoCenter(r, angle_array, w, cwidth, grating_length)
        left1c_x = nongrating[0]
        left1c_y = nongrating[1]
        left2c_x = nongrating[2]
        left2c_y = nongrating[3]
        lasti = nongrating[4]
        right1c_x = [i * -1 for i in left1c_x]
        right1c_y = [i * -1 for i in left1c_y]
        right2c_x = [i * -1 for i in left2c_x]
        right2c_y = [i * -1 for i in left2c_y]

        # Calculate the Spiral Coordinates
        # IF WANT TO CALCULATE BASED ON LENGTH OF WG that includes gratings
        # for coord in spiral_gen_NoCenter_Gratings(r,angle_array_NoCenter,w,cwidth,grating_length,lasti-1):
        for coord in spiral_gen_NoCenter_Gratings(
            r, angle_array, w, cwidth, grating_length, lasti - 1
        ):
            left_x_inc.append(coord[0])
            left_y_inc.append(coord[1])
            left_x_dec.append(coord[2])
            left_y_dec.append(coord[3])

            left2_x_inc.append(coord[4])
            left2_y_inc.append(coord[5])
            left2_x_dec.append(coord[6])
            left2_y_dec.append(coord[7])

        dx = coord[8]
        dy = coord[9]

        right1x = []
        right1y = []
        right2x = []
        right2y = []
        for coord in spiral_gen_NoCenter_Gratings(
            r, angle_array, w, 0, grating_length, lasti - 1
        ):
            right1x.append(coord[0])
            right1y.append(coord[1])
            right2x.append(coord[2])
            right2y.append(coord[3])

        # Flip coords for right side coords
        right1x = [i * -1 for i in right1x]
        right1y = [i * -1 for i in right1y]
        right2x = [i * -1 for i in right2x]
        right2y = [i * -1 for i in right2y]

        # Obtain a sorted list of the coordinates of one wall.
        # repeat for the rest
        result = sort_coord(True, left_x_inc, left_y_inc, left_x_dec, left_y_dec)
        left1x = result[0]
        left1y = result[1]
        result = sort_coord(False, left2_x_inc, left2_y_inc, left2_x_dec, left2_y_dec)
        left2x = result[0]
        left2y = result[1]

        # Center Boundary Point
        del left1x[0]
        del left1y[0]
        del left2x[0]
        del left2y[0]

        # UNIFORM SECTION

        del left1x[-1]
        del left1y[-1]
        del left2x[-1]
        del left2y[-1]

        del right1x[-1]
        del right1y[-1]
        del right2x[-1]
        del right2y[-1]

        result = finish_spiral(r, angle_array[-2], w, dx, dy)
        # IF WANT TO CALCULATE BASED ON LENGTH OF WG that includes gratings
        # result = finish_spiral(r,angle_array_NoCenter[-2],w,dx,dy)
        left1x.extend(result[0])
        left1y.extend(result[1])
        left2x.extend(result[2])
        left2y.extend(result[3])

        right1x.extend(i * -1 for i in result[0])
        right1y.extend(i * -1 for i in result[1])
        right2x.extend(i * -1 for i in result[2])
        right2y.extend(i * -1 for i in result[3])
        #########################################

        # Step3 Organize all the points into a single matrix to be drawn in klayout.
        spiral_x = []
        spiral_y = []

        spiral_x.extend(reversed(left1x))
        spiral_x.extend(reversed(left1c_x))
        spiral_x.extend(right2c_x)
        spiral_x.extend(right2x)
        spiral_x.extend(reversed(right1x))
        spiral_x.extend(reversed(right1c_x))
        spiral_x.extend(left2c_x)
        spiral_x.extend(left2x)

        spiral_y.extend(reversed(left1y))
        spiral_y.extend(reversed(left1c_y))
        spiral_y.extend(right2c_y)
        spiral_y.extend(right2y)
        spiral_y.extend(reversed(right1y))
        spiral_y.extend(reversed(right1c_y))
        spiral_y.extend(left2c_y)
        spiral_y.extend(left2y)

        # makes Dpoints from the coordinates
        dpts = [pya.DPoint(spiral_x[i], spiral_y[i]) for i in range(len(spiral_x))]
        dpolygon = DPolygon(dpts)
        # dmult_pts = mult_pts(dpts,1)

        # dpoint polygon solution thanks to Jaspreet#
        element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
        shapes(LayerSiN).insert(element)
        # shapes(LayerSiN).insert(Polygon.from_dpoly(dpolygon))

        DeviceHeight = self.cell.bbox().height() * dbu
        # WG1
        wg1 = Box(
            self.cell.bbox().width() / 2.0,
            0,
            self.cell.bbox().width() / 2.0 - 2 * w / dbu,
            DeviceHeight / dbu / 2.0,
        )
        shapes(LayerSiN).insert(wg1)
        # WG2
        wg2 = Box(
            -self.cell.bbox().width() / 2.0,
            0,
            -self.cell.bbox().width() / 2.0 + 2 * w / dbu,
            -DeviceHeight / dbu / 2.0,
        )
        shapes(LayerSiN).insert(wg2)
        """
    #waveguides, didnt use pathing because it has some rounding errors in terms of width   
    #dpts=[pya.DPoint(LendX+w, 0),pya.DPoint(LendX-w, 0),pya.DPoint(LendX-w, DeviceHeight/2.0),pya.DPoint(LendX+w, DeviceHeight/2.0 )]
    #dpolygon = DPolygon(round(dpts))
    #element = Polygon.from_dpoly(dpolygon*(1.0/dbu))
    #shapes(LayerSiN).insert(element)
    
    wvg = pya.Path([Point((self.cell.bbox().width()/2.0)-w/dbu, 0),Point((self.cell.bbox().width()/2.0)-w/dbu, DeviceHeight/dbu/2.0)], w/dbu*2.0)
    shapes(LayerSiN).insert(wvg)
    
    #dpts=[pya.DPoint(RendX+w, 0),pya.DPoint(RendX-w, 0),pya.DPoint(RendX-w, -DeviceHeight/2.0),pya.DPoint(RendX+w, -DeviceHeight/2.0 )]
    #dpolygon = DPolygon(dpts)
    #element = Polygon.from_dpoly(dpolygon*(1.0/dbu))
    #shapes(LayerSiN).insert(element)

    wvg = pya.Path([Point(-(self.cell.bbox().width()/2.0)+w/dbu, 0),Point(-(self.cell.bbox().width()/2.0)+w/dbu, -DeviceHeight/dbu/2.0)], w/dbu*2.0)
    shapes(LayerSiN).insert(wvg)
    """

        # pin = pya.Path([Point((RendX)/dbu*1.0, -DeviceHeight/2.0/dbu-PIN_LENGTH/2.0), Point((RendX)/dbu*1.0,-DeviceHeight/2.0/dbu+PIN_LENGTH/2.0)], w/dbu*2.0)
        pin = pya.Path(
            [
                Point(
                    -(self.cell.bbox().width() / 2.0) + w / dbu,
                    -DeviceHeight / 2.0 / dbu + PIN_LENGTH / 2.0,
                ),
                Point(
                    -(self.cell.bbox().width() / 2.0) + w / dbu,
                    -DeviceHeight / 2.0 / dbu - PIN_LENGTH / 2.0,
                ),
            ],
            w / dbu * 2.0,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(
            Trans.R0,
            -(self.cell.bbox().width() / 2.0) + w / dbu,
            -DeviceHeight / 2.0 / dbu,
        )
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # pin = pya.Path([Point((LendX)/dbu*1.0, DeviceHeight/2.0/dbu-PIN_LENGTH/2.0), Point((LendX)/dbu*1.0, DeviceHeight/2.0/dbu+PIN_LENGTH/2.0)], w/dbu*2.0)
        pin = pya.Path(
            [
                Point(
                    (self.cell.bbox().width() / 2.0) - w / dbu,
                    DeviceHeight / 2.0 / dbu - PIN_LENGTH / 2.0,
                ),
                Point(
                    (self.cell.bbox().width() / 2.0) - w / dbu,
                    DeviceHeight / 2.0 / dbu + PIN_LENGTH / 2.0,
                ),
            ],
            w / dbu * 2.0,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(
            Trans.R0,
            (self.cell.bbox().width() / 2.0) - w / dbu,
            DeviceHeight / 2.0 / dbu,
        )
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer
        # dev = Box((LendX)/dbu+w*MOD/dbu, -DeviceHeight/2/dbu-pin_length/2, (RendX)/dbu-w*MOD/dbu, DeviceHeight/2/dbu+pin_length/2 )
        # I literally declared the size of this box based on the other box. Lol.
        dev = Box(
            -self.cell.bbox().width() / 2.0,
            -self.cell.bbox().height() / 2.0 + PIN_LENGTH / 2.0,
            self.cell.bbox().width() / 2.0,
            self.cell.bbox().height() / 2.0 - PIN_LENGTH / 2.0,
        )
        shapes(LayerDevRecN).insert(dev)

        print("Done drawing the layout for - Spiral NoCenterBraggGrating")


class CDCSpiralBraggGrating(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(CDCSpiralBraggGrating, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("w", self.TypeDouble, "Waveguide1 Width [nm]", default=450)
        self.param("w2", self.TypeDouble, "Waveguide2 Width [nm]", default=550)
        self.param("num_periods", self.TypeInt, "Number of periods", default=400)
        self.param("Cwidth", self.TypeDouble, "Corrugation Width [nm]", default=30)
        self.param("Cwidth2", self.TypeDouble, "Corrugation Width2 [nm]", default=40)
        self.param("period", self.TypeDouble, "period [nm]", default=320)
        self.param("wgap", self.TypeDouble, "gap [nm]", default=200)
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "SpiralBraggGrating"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        from SiEPIC._globals import PIN_LENGTH
        # This is the main part of the implementation: create the layout

        # fetch the parameters
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSiN = ly.layer(LayerSi)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)

        w = self.w * 10**-3 / 2.0  # drawing from center line, only have to add half
        w2 = self.w2 * 10**-3 / 2.0  # drawing from center line, only have to add half
        # length = self.DeviceLength*1000/2.0#only drawing half and then copying
        length = self.num_periods * self.period / 2 * 1e-3
        cwidth = self.Cwidth * 10**-3 / 2.0  # same reason as width
        cwidth2 = self.Cwidth2 * 10**-3 / 2.0  # same reason as width
        grating_length = self.period / 2.0 * 10**-3
        wgap = self.wgap / 2.0 * 10**-3

        # Step1 Find the Angles of each grating#######
        angle_array = []
        for theta in angle_from_corrugation(r, length, grating_length):
            angle_array.append(theta)
        ####################

        #####################
        # Step2 Find the Coordinates of the gratings via the angles
        # TopHalf WG1
        # Wall 1
        TopW11_x_inc = []
        TopW11_y_inc = []
        TopW11_x_dec = []
        TopW11_y_dec = []
        # Wall 2
        TopW12_x_inc = []
        TopW12_y_inc = []
        TopW12_x_dec = []
        TopW12_y_dec = []

        # Top half WG2
        # Wall 1
        TopW21_x_inc = []
        TopW21_y_inc = []
        TopW21_x_dec = []
        TopW21_y_dec = []
        # Wall 2
        TopW22_x_inc = []
        TopW22_y_inc = []
        TopW22_x_dec = []
        TopW22_y_dec = []

        # Bottom Half
        # Wall 1
        BotW11_x_inc = []
        BotW11_y_inc = []
        BotW11_x_dec = []
        BotW11_y_dec = []
        # Wall 2
        BotW12_x_inc = []
        BotW12_y_inc = []
        BotW12_x_dec = []
        BotW12_y_dec = []

        # WG2
        # Wall 1
        BotW21_x_inc = []
        BotW21_y_inc = []
        BotW21_x_dec = []
        BotW21_y_dec = []
        # Wall 2
        BotW22_x_inc = []
        BotW22_y_inc = []
        BotW22_x_dec = []
        BotW22_y_dec = []

        # Calculate the Spiral Coordinates
        for coord in CDC_gen(
            r, angle_array, w, w2, cwidth, cwidth2, grating_length, wgap, 1
        ):
            TopW11_x_inc.append(coord[0])
            TopW11_y_inc.append(coord[1])
            TopW11_x_dec.append(coord[2])
            TopW11_y_dec.append(coord[3])
            TopW12_x_inc.append(coord[4])
            TopW12_y_inc.append(coord[5])
            TopW12_x_dec.append(coord[6])
            TopW12_y_dec.append(coord[7])
            TopW21_x_inc.append(coord[10])
            TopW21_y_inc.append(coord[11])
            TopW21_x_dec.append(coord[12])
            TopW21_y_dec.append(coord[13])
            TopW22_x_inc.append(coord[14])
            TopW22_y_inc.append(coord[15])
            TopW22_x_dec.append(coord[16])
            TopW22_y_dec.append(coord[17])
        dx = coord[8]  # Used for calculaing the no-grating portion
        dy = coord[9]

        for coord in CDC_gen(
            r, angle_array, w2, w, cwidth2, cwidth, grating_length, wgap, 1
        ):
            BotW21_x_inc.append(-coord[0])
            BotW21_y_inc.append(-coord[1])
            BotW21_x_dec.append(-coord[2])
            BotW21_y_dec.append(-coord[3])
            BotW22_x_inc.append(-coord[4])
            BotW22_y_inc.append(-coord[5])
            BotW22_x_dec.append(-coord[6])
            BotW22_y_dec.append(-coord[7])
            BotW11_x_inc.append(-coord[10])
            BotW11_y_inc.append(-coord[11])
            BotW11_x_dec.append(-coord[12])
            BotW11_y_dec.append(-coord[13])
            BotW12_x_inc.append(-coord[14])
            BotW12_y_inc.append(-coord[15])
            BotW12_x_dec.append(-coord[16])
            BotW12_y_dec.append(-coord[17])

        # Obtain a sorted list of the coordinates of one wall.
        # repeat for the rest
        # WG1
        result = sort_coord(
            True, TopW11_x_inc, TopW11_y_inc, TopW11_x_dec, TopW11_y_dec
        )
        TW11x = result[0]
        TW11y = result[1]
        # del TW11x[0]
        # del TW11y[0]

        result = sort_coord(
            False, TopW12_x_inc, TopW12_y_inc, TopW12_x_dec, TopW12_y_dec
        )
        TW12x = result[0]
        TW12y = result[1]

        result = sort_coord(
            False, BotW11_x_inc, BotW11_y_inc, BotW11_x_dec, BotW11_y_dec
        )
        BW11x = result[0]
        BW11y = result[1]
        # Delete the first two points as they over lap
        del BW11x[
            0
        ]  # calls the same index here because once you remove 0, 1 becomes 0, and so on and so forth
        del BW11x[0]
        del BW11y[0]
        del BW11y[0]

        result = sort_coord(
            True, BotW12_x_inc, BotW12_y_inc, BotW12_x_dec, BotW12_y_dec
        )
        BW12x = result[0]
        BW12y = result[1]
        del BW12x[0]
        del BW12x[0]
        del BW12y[0]
        del BW12y[0]

        # Delete for Uniform connection
        del TW11x[-1]
        del TW11y[-1]
        del TW12x[-1]
        del TW12y[-1]
        del BW11x[-1]
        del BW11y[-1]
        del BW12x[-1]
        del BW12y[-1]

        # WG2
        result = sort_coord(
            True, TopW21_x_inc, TopW21_y_inc, TopW21_x_dec, TopW21_y_dec
        )
        TW21x = result[0]
        TW21y = result[1]

        result = sort_coord(
            False, TopW22_x_inc, TopW22_y_inc, TopW22_x_dec, TopW22_y_dec
        )
        TW22x = result[0]
        TW22y = result[1]

        result = sort_coord(
            False, BotW21_x_inc, BotW21_y_inc, BotW21_x_dec, BotW21_y_dec
        )
        BW21x = result[0]
        BW21y = result[1]

        # Delete the first two points as they over lap
        del BW21x[
            0
        ]  # calls the same index here because once you remove 0, 1 becomes 0, and so on and so forth
        del BW21x[0]
        del BW21y[0]
        del BW21y[0]
        result = sort_coord(
            True, BotW22_x_inc, BotW22_y_inc, BotW22_x_dec, BotW22_y_dec
        )
        BW22x = result[0]
        BW22y = result[1]
        del BW22x[0]
        del BW22x[0]
        del BW22y[0]
        del BW22y[0]

        # UNIFORM SECTION
        del TW21x[-1]
        del TW21y[-1]
        del TW22x[-1]
        del TW22y[-1]
        del BW21x[-1]
        del BW21y[-1]
        del BW22x[-1]
        del BW22y[-1]

        # UNIFORM Endings
        # WG1
        result = finish_CDC(r, angle_array[-2], w, dx, dy, cwidth, wgap, 1)
        TW11x.extend(result[0])
        TW11y.extend(result[1])
        TW12x.extend(result[2])
        TW12y.extend(result[3])
        wg1x1 = result[4]  # x coord for drawing wgs later
        wg1x2 = result[5]
        result = finish_CDC(r, angle_array[-2], w, dx, dy, cwidth, wgap, -1)
        BW11x.extend(i * -1 for i in result[0])
        BW11y.extend(i * -1 for i in result[1])
        BW12x.extend(i * -1 for i in result[2])
        BW12y.extend(i * -1 for i in result[3])
        wg3x1 = -result[4]
        wg3x2 = -result[5]
        # WG2
        result = finish_CDC(r, angle_array[-2], w2, dx, dy, cwidth, wgap, -1)
        TW21x.extend(result[0])
        TW21y.extend(result[1])
        TW22x.extend(result[2])
        TW22y.extend(result[3])
        wg2x1 = result[4]
        wg2x2 = result[5]
        result = finish_CDC(r, angle_array[-2], w2, dx, dy, cwidth, wgap, 1)
        BW21x.extend(i * -1 for i in result[0])
        BW21y.extend(i * -1 for i in result[1])
        BW22x.extend(i * -1 for i in result[2])
        BW22y.extend(i * -1 for i in result[3])
        wg4x1 = -result[4]
        wg4x2 = -result[5]

        # Step3 Organize all the points into a single matrix to be drawn in klayout.
        spiral1_x = []
        spiral1_y = []
        spiral1_x.extend(reversed(TW11x))
        spiral1_x.extend(BW12x)
        spiral1_x.extend(reversed(BW11x))
        spiral1_x.extend(TW12x)
        spiral1_y.extend(reversed(TW11y))
        spiral1_y.extend(BW12y)
        spiral1_y.extend(reversed(BW11y))
        spiral1_y.extend(TW12y)
        spiral2_x = []
        spiral2_y = []
        spiral2_x.extend(reversed(TW21x))
        spiral2_x.extend(BW22x)
        spiral2_x.extend(reversed(BW21x))
        spiral2_x.extend(TW22x)
        spiral2_y.extend(reversed(TW21y))
        spiral2_y.extend(BW22y)
        spiral2_y.extend(reversed(BW21y))
        spiral2_y.extend(TW22y)

        if (
            spiral1_y[-2] < 0
        ):  # for drawing wgs laters, condition is to determine is the waveguide points up or down(since not symmetrical)
            devicetop = max(max(spiral1_y), max(spiral2_y))
            devicebot = min(min(spiral1_y), min(spiral2_y))
            pin_direction = 1  # pins have to extend out from wg, if the wg switches direction, the pins have to switch signs
        else:
            devicebot = max(max(spiral1_y), max(spiral2_y))
            devicetop = min(min(spiral1_y), min(spiral2_y))
            pin_direction = -1

        # makes Dpoints from the coordinates
        dpts = [pya.DPoint(spiral1_x[i], spiral1_y[i]) for i in range(len(spiral1_x))]
        dpolygon1 = DPolygon(dpts)
        dpts = [pya.DPoint(spiral2_x[i], spiral2_y[i]) for i in range(len(spiral2_x))]
        dpolygon2 = DPolygon(dpts)

        # dpoint polygon solution thanks to Jaspreet#
        element = Polygon.from_dpoly(dpolygon1 * (1.0 / dbu))
        shapes(LayerSiN).insert(element)
        element = Polygon.from_dpoly(dpolygon2 * (1.0 / dbu))
        shapes(LayerSiN).insert(element)

        # Create the pins, as short paths:
        devicewidthmax = max(wg1x1, wg1x2, wg2x1, wg2x2, wg3x1, wg3x2, wg4x1, wg4x2)
        devicewidthmin = min(wg1x1, wg1x2, wg2x1, wg2x2, wg3x1, wg3x2, wg4x1, wg4x2)

        # WG1
        wg1 = Box(wg1x1 / dbu, 0, wg1x2 / dbu, devicetop / dbu)
        shapes(LayerSiN).insert(wg1)
        wg2 = Box(wg2x1 / dbu, 0, wg2x2 / dbu, devicetop / dbu)
        shapes(LayerSiN).insert(wg2)
        wg3 = Box(wg3x1 / dbu, 0, wg3x2 / dbu, devicebot / dbu)
        shapes(LayerSiN).insert(wg3)
        wg4 = Box(wg4x1 / dbu, 0, wg4x2 / dbu, devicebot / dbu)
        shapes(LayerSiN).insert(wg4)

        # pin1 for wg1
        pin = pya.Path(
            [
                Point(
                    (wg1x1 + wg1x2) / 2.0 / dbu,
                    devicetop / dbu - PIN_LENGTH / 2.0 * pin_direction,
                ),
                Point(
                    (wg1x1 + wg1x2) / 2.0 / dbu,
                    devicetop / dbu + PIN_LENGTH / 2.0 * pin_direction,
                ),
            ],
            abs(wg1x1 - wg1x2) / dbu,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, (wg1x1 + wg1x2) / 2.0 / dbu, devicetop / dbu)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # pin2 for wg2
        pin = pya.Path(
            [
                Point(
                    (wg2x1 + wg2x2) / 2.0 / dbu,
                    devicetop / dbu - PIN_LENGTH / 2.0 * pin_direction,
                ),
                Point(
                    (wg2x1 + wg2x2) / 2.0 / dbu,
                    devicetop / dbu + PIN_LENGTH / 2.0 * pin_direction,
                ),
            ],
            abs(wg2x1 - wg2x2) / dbu,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, (wg2x1 + wg2x2) / 2.0 / dbu, devicetop / dbu)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # pin3 for wg3
        pin = pya.Path(
            [
                Point(
                    (wg3x1 + wg3x2) / 2.0 / dbu,
                    devicebot / dbu - PIN_LENGTH / 2.0 * pin_direction,
                ),
                Point(
                    (wg3x1 + wg3x2) / 2.0 / dbu,
                    devicebot / dbu + PIN_LENGTH / 2.0 * pin_direction,
                ),
            ],
            abs(wg3x1 - wg3x2) / dbu,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, (wg3x1 + wg3x2) / 2.0 / dbu, devicebot / dbu)
        text = Text("pin3", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # pin4 for wg4
        pin = pya.Path(
            [
                Point(
                    (wg4x1 + wg4x2) / 2.0 / dbu,
                    devicebot / dbu - PIN_LENGTH / 2.0 * pin_direction,
                ),
                Point(
                    (wg4x1 + wg4x2) / 2.0 / dbu,
                    devicebot / dbu + PIN_LENGTH / 2.0 * pin_direction,
                ),
            ],
            abs(wg4x1 - wg4x2) / dbu,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, (wg4x1 + wg4x2) / 2.0 / dbu, devicebot / dbu)
        text = Text("pin4", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer
        dev = Box(
            devicewidthmin / dbu,
            devicetop / dbu + PIN_LENGTH / 2.0 * pin_direction,
            devicewidthmax / dbu,
            devicebot / dbu - PIN_LENGTH / 2.0 * pin_direction,
        )
        shapes(LayerDevRecN).insert(dev)

        print("Done drawing the layout for - CDC Spiral")


class SpiralWaveguide(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(SpiralWaveguide, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("w", self.TypeDouble, "Waveguide Width [nm]", default=400)
        self.param(
            "DeviceLength", self.TypeDouble, "Device Path Length [mm]", default=0.5
        )
        self.param(
            "wg_spacing", self.TypeDouble, "Waveguide spacing [microns]", default=8
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "`aveguide"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        from SiEPIC._globals import PIN_LENGTH

        ly = self.layout
        shapes = self.cell.shapes
        wg_spacing = self.wg_spacing

        LayerSi = self.silayer
        LayerSiN = ly.layer(LayerSi)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)
        LayerSiN_Slab = LayerSiN

        w = self.w * 10**-3 / 2.0  # drawing from center line, only have to add half
        length = self.DeviceLength * 1000 / 2.0  # only drawing half and then copying
        cwidth = 80 * 10**-3 / 2.0  # same reason as width
        grating_length = 1000 / 2.0 * 10**-3
        # Step1 Find the Angles of each grating#######
        angle_array = []
        for theta in angle_from_corrugation(r, length, grating_length, gap=wg_spacing):
            angle_array.append(theta)
        ####################

        # Step4 Draw slab spiral
        # Step2 Find the Coordinates of the gratings via the angles
        # Wall1 of the Left
        left_xS = []
        left_yS = []
        # Wall2 of the Left
        left2_xS = []
        left2_yS = []

        # Calculate the Spiral Coordinates
        for coord in spiral_gen(r, angle_array, w, 0, grating_length, gap=wg_spacing):
            # for coord in spiral_gen_legacy(r,angle_array,sw):
            left_xS.append(coord[0])
            left_yS.append(coord[1])
            left2_xS.append(coord[2])
            left2_yS.append(coord[3])
        dx = coord[4]
        dy = coord[5]
        # Flip coords for right side coords
        right_xS = [i * -1 for i in left_xS]
        right_yS = [i * -1 for i in left_yS]
        right2_xS = [i * -1 for i in left2_xS]
        right2_yS = [i * -1 for i in left2_yS]
        # Obtain a sorted list of the coordinates of one wall.

        result = finish_spiral(r, angle_array[-1], w, dx, dy, gap=wg_spacing)
        left_xS.extend(result[0])
        left_yS.extend(result[1])
        left2_xS.extend(result[2])
        left2_yS.extend(result[3])

        right_xS.extend(i * -1 for i in result[0])
        right_yS.extend(i * -1 for i in result[1])
        right2_xS.extend(i * -1 for i in result[2])
        right2_yS.extend(i * -1 for i in result[3])
        #########################################

        # Step4.5 Organize all the points into a single matrix to be drawn in klayout.
        slab_x = []
        slab_y = []

        slab_x.extend(reversed(left_xS))
        slab_x.extend(right2_xS)
        slab_x.extend(reversed(right_xS))
        slab_x.extend(left2_xS)

        slab_y.extend(reversed(left_yS))
        slab_y.extend(right2_yS)
        slab_y.extend(reversed(right_yS))
        slab_y.extend(left2_yS)

        # makes Dpoints from the coordinates
        dptsS = [pya.DPoint(slab_x[i], slab_y[i]) for i in range(len(slab_x))]
        dpolygonS = DPolygon(dptsS)
        # dmult_pts = mult_pts(dpts,1)

        # Step6 Pins!
        # insert slab
        # dpoint polygon solution thanks to Jaspreet#
        elementS = Polygon.from_dpoly(dpolygonS * (1.0 / dbu))
        shapes(LayerSiN_Slab).insert(elementS)

        DeviceHeight = self.cell.bbox().height() * dbu
        DeviceWidthNS = (
            self.cell.bbox().width()
        )  # width of device without slab included yet, for drawing WG

        # WG1
        wg1 = Box(
            DeviceWidthNS / 2.0,
            0,
            DeviceWidthNS / 2.0 - 2 * w / dbu,
            DeviceHeight / dbu / 2.0,
        )
        shapes(LayerSiN).insert(wg1)
        # WG2
        wg2 = Box(
            -DeviceWidthNS / 2.0,
            0,
            -DeviceWidthNS / 2.0 + 2 * w / dbu,
            -DeviceHeight / dbu / 2.0,
        )
        shapes(LayerSiN).insert(wg2)

        # Pin1
        pin = pya.Path(
            [
                Point(
                    (-DeviceWidthNS / 2.0) + w / dbu,
                    -DeviceHeight / 2.0 / dbu + PIN_LENGTH / 2.0,
                ),
                Point(
                    (-DeviceWidthNS / 2.0) + w / dbu,
                    -DeviceHeight / 2.0 / dbu - PIN_LENGTH / 2.0,
                ),
            ],
            w / dbu * 2.0,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, -(DeviceWidthNS / 2.0) + w / dbu, -DeviceHeight / 2.0 / dbu)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        # Pin2
        pin = pya.Path(
            [
                Point(
                    (DeviceWidthNS / 2.0) - w / dbu,
                    DeviceHeight / 2.0 / dbu - PIN_LENGTH / 2.0,
                ),
                Point(
                    (DeviceWidthNS / 2.0) - w / dbu,
                    DeviceHeight / 2.0 / dbu + PIN_LENGTH / 2.0,
                ),
            ],
            w / dbu * 2.0,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, (DeviceWidthNS / 2.0) - w / dbu, DeviceHeight / 2.0 / dbu)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer
        # I literally declared the size of this box based on the other box. Lol.
        dev = Box(
            -self.cell.bbox().width() / 2.0,
            -self.cell.bbox().height() / 2.0 + PIN_LENGTH / 2.0,
            self.cell.bbox().width() / 2.0,
            self.cell.bbox().height() / 2.0 - PIN_LENGTH / 2.0,
        )
        shapes(LayerDevRecN).insert(dev)

        print("Done drawing the layout for - SpiralWaveguide")
