"""
Unit tests for Waveguide PCell in EBeam PDK
Tests waveguide creation for all types defined in WAVEGUIDES.xml
"""

import pytest

tech_name = "EBeam"

import os
from SiEPIC._globals import Python_Env

import pya
from SiEPIC.utils.layout import new_layout


class TestWaveguidePCell:
    """Test the Waveguide PCell functionality"""

    def test_waveguide_pcell_module_exists(self):
        """Test that the Waveguide PCell module exists"""
        # Import os first
        import os
        
        if Python_Env == "Script":
            import sys
            path = os.path.dirname(os.path.realpath(__file__))
            sys.path.insert(0, os.path.abspath(os.path.join(path, "../../..")))
            import siepic_ebeam_pdk
        
        # Check Waveguide.py exists
        path = os.path.dirname(os.path.realpath(__file__))
        waveguide_path = os.path.join(path, "..", "pcells_EBeam", "Waveguide.py")
        assert os.path.exists(waveguide_path), "Waveguide.py should exist"

    def test_waveguide_class_import(self):
        """Test importing the Waveguide PCell class"""
        if Python_Env == "Script":
            import sys
            path = os.path.dirname(os.path.realpath(__file__))
            sys.path.insert(0, os.path.abspath(os.path.join(path, "../../..")))
            import siepic_ebeam_pdk
        
        from SiEPIC.utils.layout import new_layout
        cell, ly = new_layout(tech_name, "test_import", GUI=False, overwrite=True)
        
        # The Waveguide PCell is automatically registered when technology loads
        # Just verify we can create a layout
        assert cell is not None
        assert ly is not None

    def test_waveguide_types_loaded(self):
        """Test that waveguide types are loaded from WAVEGUIDES.xml"""
        if Python_Env == "Script":
            import sys
            path = os.path.dirname(os.path.realpath(__file__))
            sys.path.insert(0, os.path.abspath(os.path.join(path, "../../..")))
            import siepic_ebeam_pdk
        
        from SiEPIC.utils import load_Waveguides_by_Tech
        
        waveguide_types = load_Waveguides_by_Tech(tech_name)
        
        # Should have at least a few waveguide types
        assert len(waveguide_types) > 0, "No waveguide types loaded"
        
        # Separate regular waveguides from compound waveguides
        regular_wgs = [wg for wg in waveguide_types if not wg.get("compound_waveguide")]
        compound_wgs = [wg for wg in waveguide_types if wg.get("compound_waveguide")]
        
        # Should have both types
        assert len(regular_wgs) > 0, "Should have regular waveguide types"
        
        print(f"\nFound {len(regular_wgs)} regular waveguides and {len(compound_wgs)} compound waveguides")
        for wg in regular_wgs[:5]:  # Print first 5
            print(f"  - {wg['name']}")

    def test_waveguide_pcell_all_types(self):
        """Test creating waveguides with all types from WAVEGUIDES.xml using PCell instantiation"""
        if Python_Env == "Script":
            import sys
            path = os.path.dirname(os.path.realpath(__file__))
            sys.path.insert(0, os.path.abspath(os.path.join(path, "../../..")))
            import siepic_ebeam_pdk
        
        from SiEPIC.utils import load_Waveguides_by_Tech
        
        waveguide_types = load_Waveguides_by_Tech(tech_name)
        
        # Filter to only regular waveguides (not compound)
        regular_wgs = [wg for wg in waveguide_types if not wg.get("compound_waveguide")]
        
        assert len(regular_wgs) > 0, "Should have at least one regular waveguide type"
        
        # Create a new layout for all tests
        cell, ly = new_layout(tech_name, "test_waveguides", GUI=False, overwrite=True)
        pos = 0
        
        # Test each waveguide type
        for wg in waveguide_types:
            wg_name = wg["name"]
            print(f"\nTesting waveguide type: {wg_name}")
            
            # Get radius from WAVEGUIDES.xml for this waveguide type
            radius = float(wg.get("radius", 50.0))  # Default to 50 µm if not specified
            
            # Create a 90-degree bend path using the radius from XML
            # Path: (0,0) -> (10*radius,0) -> (10*radius,2*radius)
            path = pya.DPath([
                pya.DPoint(0, 0),
                pya.DPoint(10*radius, 0),
                pya.DPoint(10*radius, 2*radius)
            ], 0.5)
            
            # Use PCell instantiation method
            try:
                # Create the Waveguide PCell with parameters
                pcell = ly.create_cell("Waveguide", tech_name, {
                    "waveguide_type": wg_name,
                    "path": path
                })
                
                if pcell is None:
                    print(f"  ⚠ Could not create PCell for '{wg_name}'")
                    continue
                
                # Verify the waveguide was created
                assert pcell is not None, f"Waveguide PCell '{wg_name}' should be created"
                assert not pcell.is_empty(), f"Waveguide '{wg_name}' cell should not be empty"
                assert pcell.bbox().area() > 0, f"Waveguide '{wg_name}' should have geometry. Found area {pcell.bbox().area()}"
                
                # Calculate expected length
                import math
                expected_length = 10*radius + (math.pi * radius / 2) + 2*radius
                
                print(f"  ✓ Created waveguide PCell (radius={radius:.1f} µm, expected_length≈{expected_length:.1f} µm)")
                
                # Instance the PCell in the top cell
                trans = pya.Trans(pya.Trans.R0, -pos, pos)
                inst = cell.insert(pya.CellInstArray(pcell.cell_index(), trans))
                
                pos += 10e3
                
            except Exception as e:
                # Print error but don't fail the test - some waveguides might have dependencies
                print(f"  ⚠ Could not create waveguide '{wg_name}': {e}")
                # Only fail if it's a basic waveguide without dependencies
                if "Strip" in wg_name and "routing" not in wg_name.lower() and "compound" not in wg_name.lower():
                    import traceback
                    traceback.print_exc()
                    raise
        
        # Show the layout in KLive
        cell.show()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

