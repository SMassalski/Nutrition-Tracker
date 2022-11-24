from pathlib import Path
from shutil import rmtree
from tempfile import gettempdir

import pytest
from django.conf import settings


@pytest.fixture(scope="session", autouse=True)
def remove_temporary_media_dir():
    """
    Removes the test media directory if it is a temporary directory.
    """
    yield
    media_dir = Path(settings.MEDIA_ROOT)
    if Path(gettempdir()) in media_dir.parents and media_dir.exists():
        rmtree(media_dir)
