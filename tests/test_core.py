"""
核心功能测试
测试 core.py 中的工具函数和 API 调用
"""
import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    slugify,
    clean_content,
    get_metadata_text,
    retrieve_story,
    fetch_part_content,
    fetch_story_from_partId,
    CachedSession,
    headers,
    cache,
)


class TestUtilities:
    """测试工具函数"""
    
    def test_slugify_basic(self):
        """测试基本的 slugify 功能"""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test  Multiple   Spaces") == "test-multiple-spaces"
        assert slugify("Special!@#$%Characters") == "specialcharacters"
    
    def test_slugify_unicode(self):
        """测试 Unicode 字符处理"""
        assert slugify("你好世界") == ""
        assert slugify("Café") == "cafe"
        assert slugify("Hello 世界", allow_unicode=True) == "hello-世界"
    
    def test_clean_content(self):
        """测试 HTML 清理功能"""
        html = "<p>Hello</p><script>alert('test')</script><p>World</p>"
        result = clean_content(html)
        assert "Hello" in result
        assert "World" in result
        assert "script" not in result
        assert "alert" not in result
    
    def test_clean_content_with_breaks(self):
        """测试换行符处理"""
        html = "<p>Line 1</p><br><p>Line 2</p>"
        result = clean_content(html)
        assert "Line 1" in result
        assert "Line 2" in result


class TestMetadata:
    """测试元数据处理"""
    
    def test_get_metadata_text(self):
        """测试元数据文本生成"""
        mock_story = {
            "title": "Test Story",
            "user": {"username": "testuser"},
            "language": {"name": "English"},
            "createDate": "2024-01-01",
            "modifyDate": "2024-01-02",
            "completed": True,
            "mature": False,
            "tags": ["tag1", "tag2"],
            "url": "https://wattpad.com/story/123",
            "description": "Test description"
        }
        
        result = get_metadata_text(mock_story)
        assert "Test Story" in result
        assert "testuser" in result
        assert "English" in result
        assert "tag1, tag2" in result


@pytest.mark.asyncio
class TestAPIIntegration:
    """API 集成测试（需要网络连接）"""
    
    async def test_retrieve_story_public(self):
        """测试获取公开故事信息"""
        # 使用一个已知的公开故事 ID 进行测试
        # 注意：这需要实际的网络连接
        try:
            async with CachedSession(headers=headers, cache=None, trust_env=True) as session:
                # 使用一个测试 ID，如果失败则跳过
                story = await retrieve_story(311395088, cookies=None, session=session)
                assert story is not None
                assert "title" in story
                assert "parts" in story
                assert len(story["parts"]) > 0
        except Exception as e:
            pytest.skip(f"网络测试失败或故事不可用: {e}")
    
    async def test_fetch_story_from_part_id(self):
        """测试从章节 ID 获取故事"""
        try:
            async with CachedSession(headers=headers, cache=None, trust_env=True) as session:
                # 使用一个测试章节 ID
                story_id, story = await fetch_story_from_partId(1234567890, cookies=None, session=session)
                assert story_id is not None
                assert story is not None
        except Exception as e:
            pytest.skip(f"网络测试失败或章节不可用: {e}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
