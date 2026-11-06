"""Offline credential routing checks; no real keys or network requests."""
import contextlib
import io
import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

import image_gen


class CredentialTests(unittest.TestCase):
    def test_placeholder_and_missing(self):
        for values in ({}, {'OPENAI_API_KEY': 'lm-studio'}, {'IMAGE_GEN_API_KEY': 'placeholder'}):
            with patch.dict(os.environ, values, clear=True), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    image_gen._ensure_api_key(False)
                image_gen._ensure_api_key(True)

    def test_clients_use_dedicated_key_and_official_endpoint(self):
        fake = types.ModuleType('openai')
        fake.OpenAI = Mock()
        fake.AsyncOpenAI = Mock()
        values = {'IMAGE_GEN_API_KEY': 'test-image-key', 'OPENAI_API_KEY': 'lm-studio',
                  'OPENAI_BASE_URL': 'http://localhost:1234/v1'}
        with patch.dict(os.environ, values, clear=True), patch.dict(sys.modules, {'openai': fake}):
            image_gen._create_client()
            image_gen._create_async_client()
            for constructor in (fake.OpenAI, fake.AsyncOpenAI):
                constructor.assert_called_once_with(api_key='test-image-key', base_url='https://api.openai.com/v1')
            self.assertEqual(os.environ['OPENAI_API_KEY'], 'lm-studio')

    def test_legacy_fallback(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-legacy-key'}, clear=True):
            self.assertEqual(image_gen._image_api_key(), 'test-legacy-key')

    def test_env_file_is_selective_and_environment_wins(self):
        fake = types.ModuleType('dotenv')
        fake.dotenv_values = Mock(return_value={'IMAGE_GEN_API_KEY': 'test-file-key',
                                               'OPENAI_API_KEY': 'unwanted',
                                               'OPENAI_BASE_URL': 'http://unwanted'})
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'lm-studio'}, clear=True), \
             patch.dict(sys.modules, {'dotenv': fake}), patch.object(image_gen.Path, 'is_file', return_value=True):
            image_gen._load_image_env('.env')
            self.assertEqual(image_gen._image_api_key(), 'test-file-key')
            self.assertEqual(os.environ['OPENAI_API_KEY'], 'lm-studio')
            self.assertNotIn('OPENAI_BASE_URL', os.environ)
            os.environ['IMAGE_GEN_API_KEY'] = 'test-process-key'
            image_gen._load_image_env('.env')
            self.assertEqual(image_gen._image_api_key(), 'test-process-key')
            fake.dotenv_values.assert_called_with('.env', interpolate=False)


if __name__ == '__main__':
    unittest.main()
