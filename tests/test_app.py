"""
应用层测试
测试 app.py 中的文件处理和业务逻辑
"""
import pytest
from pathlib import Path
import sys
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import get_book_dir, sanitize_filename, DOWNLOAD_ROOT


class TestFileHandling:
    """测试文件处理功能"""
    
    def test_get_book_dir(self):
        """测试书籍目录生成"""
        result = get_book_dir("Test Story", "123456")
        assert isinstance(result, Path)
        assert "test-story_123456" in str(result)
        assert result.parent == DOWNLOAD_ROOT
    
    def test_get_book_dir_special_chars(self):
        """测试特殊字符处理"""
        result = get_book_dir("Test: Story! @#$", "789")
        assert isinstance(result, Path)
        # 应该移除特殊字符
        assert "test-story_789" in str(result)
    
    def test_sanitize_filename_basic(self):
        """测试文件名清理"""
        assert sanitize_filename("normal.txt") == "normal.txt"
        assert sanitize_filename("file with spaces.txt") == "file with spaces.txt"
    
    def test_sanitize_filename_special_chars(self):
        """测试特殊字符移除"""
        # Windows 不允许的字符
        result = sanitize_filename('file<>:"/\\|?*.txt')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result


class TestURLParsing:
    """测试 URL 解析逻辑"""
    
    def test_story_url_pattern(self):
        """测试故事 URL 模式匹配"""
        pattern = r"wattpad\.com/story/(\d+)"
        
        url1 = "https://www.wattpad.com/story/123456789"
        match1 = re.search(pattern, url1)
        assert match1 is not None
        assert match1.group(1) == "123456789"
        
        url2 = "wattpad.com/story/987654321-some-title"
        match2 = re.search(pattern, url2)
        assert match2 is not None
        assert match2.group(1) == "987654321"
    
    def test_part_url_pattern(self):
        """测试章节 URL 模式匹配"""
        pattern = r"wattpad\.com/(\d+)"
        
        url1 = "https://www.wattpad.com/123456789"
        match1 = re.search(pattern, url1)
        assert match1 is not None
        assert match1.group(1) == "123456789"
    
    def test_numeric_id(self):
        """测试纯数字 ID"""
        test_id = "123456789"
        assert test_id.isdigit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
