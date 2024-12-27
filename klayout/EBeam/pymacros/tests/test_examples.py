"""
Run the examples as tests

by Lukas Chrostowski 2024

"""

import sys, os
filepath = os.path.dirname(os.path.realpath(__file__))
newpath = os.path.join(filepath,'../Example_scripted_layouts')
sys.path.append(newpath)


def test_examples():
    
    import MZI
    MZI.MZI()

    import Ring_resonator_sweep
    Ring_resonator_sweep.Ring_resonator_sweep()
    
    import Contra_directional_coupler_design
    Contra_directional_coupler_design.Contra_directional_coupler_design()
    
if __name__ == "__main__":
    test_examples()
