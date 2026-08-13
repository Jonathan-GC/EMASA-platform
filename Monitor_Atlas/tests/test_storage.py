from django.test import SimpleTestCase, override_settings
from django.core.files.storage import FileSystemStorage, storages
from storages.backends.s3 import S3Storage


class StorageConfigurationTest(SimpleTestCase):
    def test_default_file_system_storage_when_use_r2_is_false(self):
        with override_settings(
            USE_R2=False,
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                },
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                },
            },
        ):
            storage = storages["default"]
            self.assertIsInstance(storage, FileSystemStorage)

    def test_r2_s3_storage_when_use_r2_is_true(self):
        with override_settings(
            USE_R2=True,
            R2_ACCESS_KEY_ID="test_access_key",
            R2_SECRET_ACCESS_KEY="test_secret_key",
            R2_BUCKET_NAME="test_bucket",
            R2_ENDPOINT_URL="https://test_account.r2.cloudflarestorage.com",
            R2_CUSTOM_DOMAIN="https://pub-test.r2.dev",
            R2_REGION_NAME="auto",
            STORAGES={
                "default": {
                    "BACKEND": "storages.backends.s3.S3Storage",
                    "OPTIONS": {
                        "access_key": "test_access_key",
                        "secret_key": "test_secret_key",
                        "bucket_name": "test_bucket",
                        "endpoint_url": "https://test_account.r2.cloudflarestorage.com",
                        "custom_domain": "https://pub-test.r2.dev",
                        "region_name": "auto",
                        "signature_version": "s3v4",
                        "file_overwrite": False,
                        "default_acl": None,
                    },
                },
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                },
            },
        ):
            storage = storages["default"]
            self.assertIsInstance(storage, S3Storage)
            self.assertEqual(storage.bucket_name, "test_bucket")
            self.assertEqual(storage.endpoint_url, "https://test_account.r2.cloudflarestorage.com")
            self.assertEqual(storage.custom_domain, "https://pub-test.r2.dev")
