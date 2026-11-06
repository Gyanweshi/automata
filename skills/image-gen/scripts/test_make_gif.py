"""Offline behavioral checks; run with Python (Pillow required)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


class GifTests(unittest.TestCase):
    def test_encoding_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs = []
            for i, color in enumerate(('red', 'green', 'blue')):
                path = root / f'{i}.png'
                Image.new('RGB', (40, 20), color).save(path)
                inputs.append(str(path))
            output = root / 'result.gif'
            command = [sys.executable, str(Path(__file__).with_name('make_gif.py')),
                       '--frames', *inputs, '--out', str(output)]

            def run(*extra, ok=True):
                result = subprocess.run(command + list(extra), capture_output=True, text=True)
                self.assertEqual(result.returncode == 0, ok, result.stderr)

            run('--duration-ms', '100', '200', '300', '--ping-pong', '--width', '20')
            with Image.open(output) as gif:
                self.assertEqual(gif.size, (20, 10))
                self.assertEqual(gif.info['loop'], 0)
                self.assertEqual(gif.n_frames, 4)
                for i, (color, duration) in enumerate(zip(
                    ((255, 0, 0), (0, 128, 0), (0, 0, 255), (0, 128, 0)),
                    (100, 200, 300, 200),
                )):
                    gif.seek(i)
                    self.assertEqual(gif.convert('RGB').getpixel((5, 5)), color)
                    self.assertEqual(gif.info['duration'], duration)
            original = output.read_bytes()
            run(ok=False)
            self.assertEqual(output.read_bytes(), original)
            run('--force', '--loop', '-1')
            with Image.open(output) as gif:
                self.assertNotIn('loop', gif.info)
            run('--force', '--fps', '0', ok=False)
            run('--force', '--duration-ms', '100', ok=False)
            Image.new('RGB', (41, 20)).save(inputs[1])
            run('--force', ok=False)
            Image.new('RGBA', (40, 20), (255, 0, 0, 0)).save(inputs[1])
            run('--force', ok=False)
            run('--force', '--matte', '#ffffff')
            with Image.open(output) as gif:
                gif.seek(1)
                self.assertEqual(gif.convert('RGB').getpixel((5, 5)), (255, 255, 255))


if __name__ == '__main__':
    unittest.main()
