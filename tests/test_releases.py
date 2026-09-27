import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coma.releases import ReleaseError, download_latest


class ReleaseDownloadTests(unittest.TestCase):
    def _release(self, content: bytes, *, digest: str | None = None, url: str | None = None) -> bytes:
        return json.dumps({
            "tag_name": "v0.1.0",
            "assets": [{
                "name": "CoMa-Windows.zip",
                "state": "uploaded",
                "digest": digest or "sha256:" + hashlib.sha256(content).hexdigest(),
                "browser_download_url": url or "https://github.com/Lord-physics/CoMa/releases/download/v0.1.0/CoMa-Windows.zip",
            }],
        }).encode()

    def test_downloads_verified_zip(self):
        content = b"example package"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CoMa-Windows.zip"
            with patch("coma.releases.urllib.request.urlopen", side_effect=[io.BytesIO(self._release(content)), io.BytesIO(content)]):
                self.assertEqual(download_latest(path), "v0.1.0")
            self.assertEqual(path.read_bytes(), content)

    def test_bad_digest_keeps_previous_file_and_removes_partial_download(self):
        content = b"invalid package"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CoMa-Windows.zip"
            path.write_bytes(b"previous package")
            with patch("coma.releases.urllib.request.urlopen", side_effect=[
                io.BytesIO(self._release(content, digest="sha256:" + "0" * 64)), io.BytesIO(content)
            ]):
                with self.assertRaises(ReleaseError):
                    download_latest(path)
            self.assertEqual(path.read_bytes(), b"previous package")
            self.assertEqual(list(Path(directory).glob("*.part")), [])

    def test_rejects_unexpected_asset_host_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("coma.releases.urllib.request.urlopen", return_value=io.BytesIO(self._release(
                b"content", url="https://example.com/CoMa-Windows.zip"
            ))) as request:
                with self.assertRaises(ReleaseError):
                    download_latest(Path(directory) / "CoMa-Windows.zip")
            self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
