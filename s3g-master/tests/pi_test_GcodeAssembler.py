import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import makerbot_driver
from makerbot_driver.GcodeAssembler import GcodeRecipes

class TestGcodeAssembler(unittest.TestCase):
    def setUp(self):
        self.profile = makerbot_driver.Profile('ReplicatorDual')
        self.ga = makerbot_driver.GcodeAssembler(self.profile)
        self.recipes = GcodeRecipes

    def tearDown(self):
        self.ga = None

    def test_get_recipes_and_variables(self):
        cases = ['ABS', 'PLA', 'dualstrusion']
        for case in cases:
            values = self.recipes[case]
            start_sequence = values['print_start_sequence']
            end_sequence = values['print_end_sequence']
            variables = values['variables']
            expected_values = (start_sequence, end_sequence, variables)
            got_values = self.ga.get_recipes_and_variables(case)
            self.assertEqual(expected_values, got_values)

    def test_recipe_not_found(self):
        with self.assertRaises(makerbot_driver.RecipeNotFoundError):
            self.ga.get_recipes_and_variables('this_isnt_a_recipe')

    def test_assemble_gcode_dualstrusion_pla(self):
        expected_start_template = {
            'begin_print': 'replicator_begin',
            'homing': 'replicator_homing',
            'start_position': 'replicator_start_position',
            'heat_platform': 'no_heat',
            'heat_tools': 'dualstrusion',
            'end_start_sequence': 'replicator_end_start_sequence',
        }
        expected_end_template = {
            'end_position': 'replicator_end_position',
            'cool_platform': 'no_cool',
            'cool_tools': 'dualstrusion',
            'end_print': 'replicator_end',
        }
        expected_variables = {
            'TOOL_0_TEMP': 230,
            'TOOL_1_TEMP': 230,
        }
        got_start, got_end, got_variables = self.ga.assemble_recipe(
            tool_0=True, tool_1=True, material='PLA')
        for expect, got in zip([expected_start_template, expected_end_template, expected_variables], [got_start, got_end, got_variables]):
            self.assertEqual(expect, got)

    def test_assemble_gcode_tool_0_pla(self):
        expected_start_template = {
            'begin_print': 'replicator_begin',
            'homing': 'replicator_homing',
            'start_position': 'replicator_start_position',
            'heat_platform': 'no_heat',
            'heat_tools': 'heat_0',
            'end_start_sequence': 'replicator_end_start_sequence',
        }
        expected_end_template = {
            'end_position': 'replicator_end_position',
            'cool_platform': 'no_cool',
            'cool_tools': 'cool_0',
            'end_print': 'replicator_end',
        }
        expected_variables = {
            'TOOL_0_TEMP': 230,
            'TOOL_1_TEMP': 230,
        }
        got_start, got_end, got_variables = self.ga.assemble_recipe(
            material='PLA')
        for expect, got in zip([expected_start_template, expected_end_template, expected_variables], [got_start, got_end, got_variables]):
            self.assertEqual(expect, got)

    def test_assemble_gcode_tool_1_pla(self):
        expected_start_template = {
            'begin_print': 'replicator_begin',
            'homing': 'replicator_homing',
            'start_position': 'replicator_start_position',
            'heat_platform': 'no_heat',
            'heat_tools': 'heat_1',
            'end_start_sequence': 'replicator_end_start_sequence',
        }
        expected_end_template = {
            'end_position': 'replicator_end_position',
            'cool_platform': 'no_cool',
            'cool_tools': 'cool_1',
            'end_print': 'replicator_end',
        }
        expected_variables = {
            'TOOL_0_TEMP': 230,
            'TOOL_1_TEMP': 230,
        }
        got_start, got_end, got_variables = self.ga.assemble_recipe(
            tool_0=False, tool_1=True, material='PLA')
        for expect, got in zip([expected_start_template, expected_end_template, expected_variables], [got_start, got_end, got_variables]):
            self.assertEqual(expect, got)

    def test_assemble_gcode_tool_1_pla_heat_platform_override(self):
        expected_start_template = {
            'begin_print': 'replicator_begin',
            'homing': 'replicator_homing',
            'start_position': 'replicator_start_position',
            'heat_platform': 'heat_platform',
            'heat_tools': 'heat_1',
            'end_start_sequence': 'replicator_end_start_sequence',
        }
        expected_end_template = {
            'end_position': 'replicator_end_position',
            'cool_platform': 'cool_platform',
            'cool_tools': 'cool_1',
            'end_print': 'replicator_end',
        }
        expected_variables = {
            'TOOL_0_TEMP': 230,
            'TOOL_1_TEMP': 230,
        }
        got_start, got_end, got_variables = self.ga.assemble_recipe(
            tool_0=False, tool_1=True, material='PLA', heat_platform_override=True)
        for expect, got in zip([expected_start_template, expected_end_template, expected_variables], [got_start, got_end, got_variables]):
            self.assertEqual(expect, got)

    def test_assemble_gcode_dualstrusion_abs(self):
        expected_start_template = {
            'begin_print': 'replicator_begin',
            'homing': 'replicator_homing',
            'start_position': 'replicator_start_position',
            'heat_platform': 'heat_platform',
            'heat_tools': 'dualstrusion',
            'end_start_sequence': 'replicator_end_start_sequence',
        }
        expected_end_template = {
            'end_position': 'replicator_end_position',
            'cool_platform': 'cool_platform',
            'cool_tools': 'dualstrusion',
            'end_print': 'replicator_end',
        }
        expected_variables = {
            'TOOL_0_TEMP': 230,
            'TOOL_1_TEMP': 230,
            'PLATFORM_TEMP': 110
        }
        got_start, got_end, got_variables = self.ga.assemble_recipe(
            tool_1=True, material='ABS')
        for expect, got in zip([expected_start_template, expected_end_template, expected_variables], [got_start, got_end, got_variables]):
            self.assertEqual(expect, got)

    def test_assemble_gcode_dualstrusion_abs_no_heat_platform_override(self):
        expected_start_template = {
            'begin_print': 'replicator_begin',
            'homing': 'replicator_homing',
            'start_position': 'replicator_start_position',
            'heat_platform': None,
            'heat_tools': 'dualstrusion',
            'end_start_sequence': 'replicator_end_start_sequence',
        }
        expected_end_template = {
            'end_position': 'replicator_end_position',
            'cool_platform': None,
            'cool_tools': 'dualstrusion',
            'end_print': 'replicator_end',
        }
        expected_variables = {
            'TOOL_0_TEMP': 230,
            'TOOL_1_TEMP': 230,
            'PLATFORM_TEMP': 110
        }
        got_start, got_end, got_variables = self.ga.assemble_recipe(
            tool_1=True, material='ABS', no_heat_platform_override=True)
        for expect, got in zip([expected_start_template, expected_end_template, expected_variables], [got_start, got_end, got_variables]):
            self.assertEqual(expect, got)

    def test_assemble_start_gcode(self):
        the_order = [
            'begin_print',
            'homing',
            'start_position',
            'heat_platform',
            'heat_tools',
            'end_start_sequence',
        ]

        recipe = {
            'begin_print': 'replicator_begin',
            'homing': 'replicator_homing',
            'start_position': 'replicator_start_position',
            'heat_platform': 'no_heat',
            'heat_tools': 'dualstrusion',
            'end_start_sequence': 'replicator_end_start_sequence'
        }
        start_sequence = self.profile.values['print_start_sequence']
        expected_gcode = []
        for routine in the_order:
            expected_gcode.extend(start_sequence[routine][recipe[routine]])
        got_gcode = self.ga.assemble_start_sequence(recipe)
        self.assertEqual(expected_gcode, got_gcode)

    def test_assemble_end_gcode(self):
        the_order = [
            'end_position',
            'cool_platform',
            'cool_tools',
            'end_print',
        ]
        recipe = {
            'end_position': 'replicator_end_position',
            'cool_platform': 'no_cool',
            'cool_tools': 'dualstrusion',
            'end_print': 'replicator_end',
        }
        end_sequence = self.profile.values['print_end_sequence']
        expected_gcode = []
        for routine in the_order:
            expected_gcode.extend(end_sequence[routine][recipe[routine]])
        got_gcode = self.ga.assemble_end_sequence(recipe)
        self.assertEqual(expected_gcode, got_gcode)

    def test_assemble_sequence_from_recipe_nones(self):
        the_order = [
            'end_position',
            'cool_platform',
            'cool_tools',
            'end_print',
        ]
        template = "print_end_sequence"
        recipe = {
            'end_position': None,
            'cool_platform': None,
            'cool_tools': None,
            'end_print': None,
        }
        expected_sequence = []
        self.assertEqual(expected_sequence, self.ga.assemble_sequence_from_recipe(recipe, template, the_order))

    def test_assemble_sequence_from_recipe_half_nones(self):
        the_order = [
            'end_position',
            'cool_platform',
            'cool_tools',
            'end_print',
        ]
        recipe = {
            'end_position': None,
            'cool_platform': 'cool_platform',
            'cool_tools': 'cool_0',
            'end_print': None,
        }
        template = "print_end_sequence"
        end_sequence_template = self.profile.values['print_end_sequence']
        expected_sequence = []
        for routine in the_order:
            if recipe[routine] is not None:
                expected_sequence.extend(
                    end_sequence_template[routine][recipe[routine]])
        self.assertEqual(expected_sequence, self.ga.assemble_sequence_from_recipe(recipe, template, the_order))
if __name__ == '__main__':
    unittest.main()
