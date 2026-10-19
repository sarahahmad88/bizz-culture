from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def button(app, label):
    return next(b for b in app.button if b.label == label)


class UITests(unittest.TestCase):
    def test_full_demo_retry_progress_and_delete(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=25).run()
        self.assertFalse(app.exception)
        app.sidebar.radio[0].set_value("Start training").run()
        button(app, "Create my scenario").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["attempt"]["status"], "ready")
        button(app, "Begin conversation").click().run()
        # Empty submissions preserve the round.
        button(app, "Send response").click().run()
        self.assertTrue(app.error)
        self.assertEqual(len(app.session_state["attempt"]["turns"]), 0)
        for i in range(3):
            app.text_area[0].set_value(f"Could we discuss testing option {i+1} together?")
            button(app, "Send response").click().run()
            self.assertFalse(app.exception)
        button(app, "Get my response scores").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["attempt"]["result"]["overall"], 60)
        self.assertEqual(app.session_state["attempt"]["calls"], 0)
        self.assertEqual(len(app.session_state["history"]), 1)
        original = app.session_state["attempt"]["id"]
        button(app, "Try the same scenario again").click().run()
        self.assertEqual(app.session_state["attempt"]["parent_id"], original)
        for page in ["Progress", "Learn", "Settings"]:
            app.sidebar.radio[0].set_value(page).run()
            self.assertFalse(app.exception)
        button(app, "Delete active attempt and session history").click().run()
        self.assertIsNone(app.session_state["attempt"])
        self.assertEqual(app.session_state["history"], [])

    def test_live_missing_key_validation_and_early_exit(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=25).run()
        app.sidebar.radio[0].set_value("Start training").run()
        app.sidebar.radio[1].set_value("Live Groq").run()
        button(app, "Create my scenario").click().run()
        self.assertTrue(app.error)
        self.assertIsNone(app.session_state["attempt"])
        app.sidebar.radio[1].set_value("Demo").run()
        button(app, "Create my scenario").click().run()
        button(app, "Begin conversation").click().run()
        button(app, "End attempt early").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["attempt"]["status"], "incomplete")
        self.assertEqual(app.session_state["history"], [])


if __name__ == "__main__":
    unittest.main()
