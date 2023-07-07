import unittest
from types import ModuleType
from typing import Optional

from linkml_runtime.loaders import json_loader
from linkml_runtime.utils.compile_python import compile_python

from linkml.generators.pythongen import PythonGenerator
from tests.test_generators.environment import env

SCHEMA = env.input_path("kitchen_sink.yaml")
PYTHON = env.expected_path("kitchen_sink.py")
MLM_SCHEMA = env.input_path("kitchen_sink_mlm.yaml")
MLM_PYTHON = env.expected_path("kitchen_sink_mlm.py")
DATA = env.input_path("kitchen_sink_inst_01.yaml")


def make_python(infile, outfile, save: Optional[bool] = False) -> ModuleType:
    """
    Note: if you change the yaml schema and associated test instance objects,
    you may need to run this test twice
    """
    pstr = str(PythonGenerator(infile, mergeimports=True).serialize())
    kitchen_module = compile_python(pstr)
    if save:
        with open(outfile, "w") as io:
            io.write(pstr)
    return kitchen_module


class PythonGenTestCase(unittest.TestCase):
    def test_pythongen(self):
        """python"""
        kitchen_module = make_python(SCHEMA, PYTHON, True)
        c = kitchen_module.Company("ROR:1")
        self.assertEqual("Company(id='ROR:1', name=None, aliases=[], ceo=None)", str(c))
        h = kitchen_module.EmploymentEvent(employed_at=c.id)
        self.assertEqual(
            "EmploymentEvent(started_at_time=None, ended_at_time=None, is_current=None, "
            "metadata=None, employed_at='ROR:1', type=None)",
            str(h),
        )
        p = kitchen_module.Person("P:1", has_employment_history=[h])
        assert p.id == "P:1"
        assert p.has_employment_history[0] is not None
        assert p.has_employment_history[0].employed_at == c.id
        # self.assertEqual("Person(id='P:1', name=None, has_employment_history=[EmploymentEvent(started_at_time=None, "
        #                 "ended_at_time=None, is_current=None, employed_at='ROR:1')], has_familial_relationships=[], "
        #                 "has_medical_history=[], age_in_years=None, addresses=[], aliases=[])", str(p))

        # Inline lists work:
        p2dict = {
            "id": "P:2",
            "addresses": [{"street": "1 foo street", "city": "foo city"}],
        }
        json_loader.loads(p2dict, kitchen_module.Person)

        # however, inline in a non-list context does not
        p2dict = {"id": "P:2", "has_birth_event": {"started_at_time": "1981-01-01"}}
        json_loader.loads(p2dict, kitchen_module.Person)
        self.assertEqual(
            "Person(id='P:1', name=None, has_employment_history=[EmploymentEvent(started_at_time=None, "
            "ended_at_time=None, is_current=None, metadata=None, employed_at='ROR:1', type=None)], "
            "has_familial_relationships=[], has_medical_history=[], age_in_years=None, addresses=[], "
            "has_birth_event=None, species_name=None, stomach_count=None, is_living=None, aliases=[])",
            str(p),
        )

        f = kitchen_module.FamilialRelationship(
            related_to="me", type="SIBLING_OF", cordialness="heartfelt"
        )
        self.assertEqual(
            "FamilialRelationship(started_at_time=None, ended_at_time=None, related_to='me', "
            "type='SIBLING_OF', cordialness=(text='heartfelt', description='warm and hearty friendliness'))",
            str(f),
        )

        diagnosis = kitchen_module.DiagnosisConcept(id="CODE:D0001", name="headache")
        event = kitchen_module.MedicalEvent(in_location="GEO:1234", diagnosis=diagnosis)
        self.assertEqual(
            "MedicalEvent(started_at_time=None, ended_at_time=None, is_current=None, "
            "metadata=None, in_location='GEO:1234', diagnosis=DiagnosisConcept(id='CODE:D0001', "
            "name='headache', in_code_system=None), procedure=None)",
            str(event),
        )

    def test_multiline_stuff(self):
        multi_line_module = make_python(MLM_SCHEMA, MLM_PYTHON, True)

        assert (
            multi_line_module.EmploymentEventType.PROMOTION.description
            == 'This refers to some sort of promotion event.")\n\n\nimport os\n'
            "print('DELETING ALL YOUR STUFF. HA HA HA.')"
        )


if __name__ == "__main__":
    unittest.main()
