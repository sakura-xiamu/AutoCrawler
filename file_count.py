import os
from collections import defaultdict


def analyze_directory(path):
    # 初始化统计
    stats = {
        'total_files': 0,
        'total_dirs': 0,
        'extensions': defaultdict(int),
        'size': 0
    }

    for root, dirs, files in os.walk(path):
        stats['total_dirs'] += len(dirs)
        stats['total_files'] += len(files)

        for file in files:
            file_path = os.path.join(root, file)
            # 获取文件扩展名
            ext = os.path.splitext(file)[1].lower()
            stats['extensions'][ext] += 1
            # 获取文件大小
            try:
                stats['size'] += os.path.getsize(file_path)
            except OSError:
                continue

    return stats


# 使用示例
path = "download\images_file"
stats = analyze_directory(path)
print(f"文件总数: {stats['total_files']}")
print(f"文件夹总数: {stats['total_dirs']}")
print(f"总大小: {stats['size'] / (1024 * 1024):.2f} MB")
print("\n文件类型统计:")
for ext, count in stats['extensions'].items():
    print(f"{ext or '无扩展名'}: {count}")
