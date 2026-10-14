import unittest

from waste_ops import classify_material, order_stops_nearest_neighbor, priority_label, priority_score


class WasteOperationsTests(unittest.TestCase):
    def test_classifies_common_materials_and_unknowns(self):
        self.assertEqual(classify_material("used AA battery"), "Hazardous")
        self.assertEqual(classify_material("glass bottle"), "Recyclable")
        self.assertIsNone(classify_material("mystery object"))
        self.assertIsNone(classify_material("   "))

    def test_priority_uses_fill_and_collection_age(self):
        self.assertEqual(priority_score(0, 0), 0)
        self.assertEqual(priority_score(100, 7), 100)
        self.assertEqual(priority_score(120, -2), 75)
        self.assertEqual(priority_label(75), "Urgent")
        self.assertEqual(priority_label(44), "On track")

    def test_route_starts_with_nearest_stop(self):
        depot = {"lat": 0.0, "lon": 0.0}
        close = {"id": "close", "lat": 0.0, "lon": 0.1}
        far = {"id": "far", "lat": 0.0, "lon": 1.0}
        result = order_stops_nearest_neighbor([far, close], depot)
        self.assertEqual([stop["id"] for stop in result], ["close", "far"])


if __name__ == "__main__":
    unittest.main()
