"""
测试运行脚本
执行所有测试并生成报告
"""
import subprocess
import sys
from pathlib import Path


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行 Wattpad Downloader 测试套件")
    print("=" * 60)
    print()
    
    # 确保在项目根目录
    project_root = Path(__file__).parent.parent
    
    # 运行 pytest
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(project_root / "tests"),
        "-v",
        "--tb=short",
        "--color=yes",
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=project_root)
    
    print()
    print("=" * 60)
    if result.returncode == 0:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
