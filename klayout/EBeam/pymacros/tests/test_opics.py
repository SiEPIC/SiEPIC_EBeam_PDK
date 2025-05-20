

#  Unit test for simulation using OPICS


import pytest
@pytest.mark.skip(reason="Running this test modifies the compact models, breaking them.")
def test_opics():
    import SiEPIC

    # using https://github.com/siepic/opics
    # in SiEPIC-Tools
    import SiEPIC.opics as opics
    from SiEPIC.opics.network import Network
    from SiEPIC.opics.globals import C

    import siepic_ebeam_pdk

    import sys, os
    sys.path.append( os.path.abspath (os.path.join( os.path.dirname( os.path.abspath(__file__)), '..')))
    import opics_ebeam
    
    ebeam_lib = opics_ebeam

    print(f"Components: {ebeam_lib.components_list}")

    # Create a Mach-Zehnder circuit simulation
    import numpy as np
    freq = np.linspace(C * 1e6 / 1.45, C * 1e6 / 1.61, 5000)
    circuit = Network(network_id="circuit_name", f=freq)

    input_gc = circuit.add_component(ebeam_lib.GC)
    y = circuit.add_component(ebeam_lib.Y)
    wg2 = circuit.add_component(ebeam_lib.ebeam_wg_integral_1550, params=dict(wg_length=40e-6))
    wg1 = circuit.add_component(ebeam_lib.Waveguide, params={"length":15e-6})
    y2 = circuit.add_component(ebeam_lib.Y)
    output_gc = circuit.add_component(ebeam_lib.GC)

    input_gc.set_port_reference(0, "input_port")
    output_gc.set_port_reference(0, "output_port")

    circuit.connect(input_gc, 1, y, 0)
    circuit.connect(y, 1, wg1, 0)
    circuit.connect(y, 2, wg2, 0)
    circuit.connect(y2, 0, output_gc, 1)
    circuit.connect(wg1, 1, y2, 1)
    circuit.connect(wg2, 1, y2, 2)

    circuit.simulate_network()

    result = circuit.sim_result.get_data()
    wavelengths = C/circuit.f
    transmission = result['S_0_1']
    reflection = result['S_0_0']
    
    print(len(transmission))

    assert len(transmission)==5000

if __name__ == "__main__":
    test_opics()
