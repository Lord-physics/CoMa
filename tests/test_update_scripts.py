import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path

from coma.releases import cleanup_prepared_update


ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(os.name == "nt", "Windows PowerShell is required")
class UpdateScriptTests(unittest.TestCase):
    def test_installer_replaces_files_without_admin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "package"
            package.mkdir()
            shutil.copy2(ROOT / "scripts" / "Install-CoMa.ps1", package / "Install-CoMa.ps1")
            (package / "CoMa.exe").write_bytes(b"new version")
            (package / "Uninstall-CoMa.ps1").write_text("# new uninstall", encoding="utf-8")
            (package / "actualizar.ps1").write_text("# new updater", encoding="utf-8")
            (package / "oauth-clients.json").write_text('{"microsoft": "new"}', encoding="utf-8")
            installed = root / "local" / "Programs" / "CoMa"
            installed.mkdir(parents=True)
            (installed / "CoMa.exe").write_bytes(b"old version")
            (installed / "Uninstall-CoMa.ps1").write_text("# old uninstall", encoding="utf-8")
            (installed / "actualizar.ps1").write_text("# old updater", encoding="utf-8")
            (installed / "oauth-clients.json").write_text('{"microsoft": "old"}', encoding="utf-8")
            start_menu = root / "roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            start_menu.mkdir(parents=True)
            env = {**os.environ, "LOCALAPPDATA": str(root / "local"), "APPDATA": str(root / "roaming")}
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 str(package / "Install-CoMa.ps1"), "-NoLaunch"],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((installed / "CoMa.exe").read_bytes(), b"new version")
            self.assertEqual((installed / "actualizar.ps1").read_text(), "# new updater")
            self.assertEqual((installed / "oauth-clients.json").read_text(), '{"microsoft": "new"}')
            self.assertEqual(list(installed.glob("*.backup-*")), [])

    def test_installer_restores_previous_executable_after_copy_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "package"
            package.mkdir()
            shutil.copy2(ROOT / "scripts" / "Install-CoMa.ps1", package / "Install-CoMa.ps1")
            (package / "CoMa.exe").write_bytes(b"new version")
            installed = root / "local" / "Programs" / "CoMa"
            installed.mkdir(parents=True)
            (installed / "CoMa.exe").write_bytes(b"old version")
            (installed / "Uninstall-CoMa.ps1").write_text("# old uninstall", encoding="utf-8")
            (installed / "actualizar.ps1").write_text("# old updater", encoding="utf-8")
            env = {**os.environ, "LOCALAPPDATA": str(root / "local"), "APPDATA": str(root / "roaming")}
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 str(package / "Install-CoMa.ps1"), "-NoLaunch"],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((installed / "CoMa.exe").read_bytes(), b"old version")
            self.assertEqual((installed / "actualizar.ps1").read_text(), "# old updater")
            self.assertEqual(list(installed.glob("*.backup-*")), [])

    def test_helper_installs_preverified_package_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "installed.txt"
            source = Path(tempfile.gettempdir()) / ("CoMa-update-" + uuid.uuid4().hex)
            source.mkdir()
            package = source / "CoMa-Windows.zip"
            try:
                with zipfile.ZipFile(package, "w") as archive:
                    archive.writestr("CoMa.exe", b"fake executable")
                    archive.writestr("Install-CoMa.ps1", "param([switch]$NoLaunch)\n"
                                     f"Set-Content -LiteralPath '{marker}' -Value 'installed'\n")
                digest = hashlib.sha256(package.read_bytes()).hexdigest()
                running_app = subprocess.Popen(
                    ["powershell.exe", "-NoProfile", "-Command", "Start-Sleep -Seconds 2"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                try:
                    result = subprocess.run(
                        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                         str(ROOT / "actualizar.ps1"), "-PackagePath", str(package),
                         "-ExpectedHash", digest, "-WaitForProcessId", str(running_app.pid), "-NoLaunch"],
                        capture_output=True, text=True, timeout=30,
                    )
                    self.assertIsNotNone(running_app.poll())
                finally:
                    if running_app.poll() is None:
                        running_app.terminate()
                        running_app.wait(timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(marker.read_text().strip(), "installed")
                self.assertFalse(source.exists())
            finally:
                cleanup_prepared_update(package)

    def test_installed_helper_replaces_running_script_and_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installed = root / "local" / "Programs" / "CoMa"
            installed.mkdir(parents=True)
            (installed / "CoMa.exe").write_bytes(b"old executable")
            (installed / "Uninstall-CoMa.ps1").write_text("# old uninstall", encoding="utf-8")
            shutil.copy2(ROOT / "actualizar.ps1", installed / "actualizar.ps1")
            (root / "roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs").mkdir(parents=True)
            source = Path(tempfile.gettempdir()) / ("CoMa-update-" + uuid.uuid4().hex)
            source.mkdir()
            package = source / "CoMa-Windows.zip"
            try:
                with zipfile.ZipFile(package, "w") as archive:
                    archive.writestr("CoMa.exe", b"new executable")
                    archive.write(ROOT / "scripts" / "Install-CoMa.ps1", "Install-CoMa.ps1")
                    archive.writestr("Uninstall-CoMa.ps1", "# new uninstall")
                    archive.write(ROOT / "actualizar.ps1", "actualizar.ps1")
                digest = hashlib.sha256(package.read_bytes()).hexdigest()
                env = {**os.environ, "LOCALAPPDATA": str(root / "local"), "APPDATA": str(root / "roaming")}
                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                     str(installed / "actualizar.ps1"), "-PackagePath", str(package),
                     "-ExpectedHash", digest, "-NoLaunch"],
                    env=env, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((installed / "CoMa.exe").read_bytes(), b"new executable")
                self.assertEqual((installed / "actualizar.ps1").read_bytes(), (ROOT / "actualizar.ps1").read_bytes())
                self.assertFalse(source.exists())
                self.assertEqual(list(installed.glob("*.backup-*")), [])
            finally:
                cleanup_prepared_update(package)


if __name__ == "__main__":
    unittest.main()
