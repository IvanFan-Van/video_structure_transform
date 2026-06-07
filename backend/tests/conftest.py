from pathlib import Path

import pytest


@pytest.fixture
def sample_video():
    path = Path("tests/videos/1.mp4")
    if not path.exists():
        pytest.skip("测试视频不存在")
    return path
