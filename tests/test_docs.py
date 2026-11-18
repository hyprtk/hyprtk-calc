"""Documentation and packaging checks: the ones a normal test run forgets."""

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


class Docs(unittest.TestCase):
    def test_readme_exists(self):
        text = read("README.md")
        self.assertIn("hyprtk-calc", text)
        self.assertIn("## Usage", text)

    def test_changelog_starts_with_the_shipped_version(self):
        from hyprtk_calc import __version__

        text = read("CHANGELOG.md")
        self.assertIn(__version__, text.split("\n\n")[1])

    def test_relative_links_resolve(self):
        text = read("README.md")
        missing = []
        for target in re.findall(r"\]\((?!https?:|#)([^)]+)\)", text):
            path = target.split("#")[0]
            if path and not os.path.exists(os.path.join(ROOT, path)):
                missing.append(target)
        self.assertEqual(missing, [], "README links to missing files: {0}".format(missing))

    def test_images_are_tracked(self):
        # A `.gitignore` with `docs/*.png` silently drops new screenshots, and
        # the README then renders a broken image on GitHub.
        if not os.path.isdir(os.path.join(ROOT, ".git")):
            self.skipTest("not a git checkout")
        import subprocess

        text = read("README.md")
        images = [t for t in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text) if not t.startswith("http")]
        for image in images:
            tracked = subprocess.run(
                ["git", "-C", ROOT, "ls-files", "--error-unmatch", image],
                capture_output=True,
            )
            self.assertEqual(tracked.returncode, 0, "{0} is not tracked by git".format(image))


class Packaging(unittest.TestCase):
    def test_desktop_entry(self):
        text = read("hyprtk-calc.desktop")
        self.assertIn("Exec=hyprtk-calc", text)
        self.assertIn("Icon=hyprtk-calc", text)
        self.assertIn("Categories=Utility;Calculator;", text)
        self.assertIn("StartupWMClass=hyprtk-calc", text)

    def test_assets_exist(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "hyprtk_calc/assets/hyprtk-calc.svg")))
        self.assertTrue(
            os.path.exists(os.path.join(ROOT, "hyprtk_calc/assets/hyprtk-calc-small.svg"))
        )
        self.assertTrue(
            os.path.exists(os.path.join(ROOT, "hyprtk_calc/assets/fonts/SymbolsNerdFont-Regular.ttf"))
        )

    def test_icon_is_the_suite_cut(self):
        text = read("hyprtk_calc/assets", "hyprtk-calc.svg")
        self.assertIn("512", text)

    def test_installer_mentions_every_payload(self):
        text = read("install.sh")
        self.assertIn("hyprtk_calc", text)
        self.assertIn("hyprtk-calc.desktop", text)
        self.assertIn("--system", text)

    def test_qml_files_are_packaged(self):
        text = read("pyproject.toml")
        self.assertIn("qml/components/*", text)
        self.assertIn("assets/fonts/*.ttf", text)


if __name__ == "__main__":
    unittest.main()
