import os
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties

# Windows 宿主机字体路径
host_font_path = r"C:\Windows\Fonts\msyh.ttc"
# 如果容器中挂载了该字体文件，可通过环境变量指定
container_font_path = os.environ.get("MSYH_FONT_PATH", host_font_path)

if os.path.exists(host_font_path):
    font_path = host_font_path
elif os.path.exists(container_font_path):
    font_path = container_font_path
else:
    raise FileNotFoundError(
        f"Font file not found. Please mount C:\\Windows\\Fonts\\msyh.ttc into the container or set MSYH_FONT_PATH.\n"
        f"Attempted paths: {host_font_path}, {container_font_path}"
    )

font_prop = FontProperties(fname=font_path)

# 容器内 CSV 路径示例，确保使用 /mnt/f 挂载路径
csv_path = "/mnt/f/vs-code-openclaw/data/example.csv"

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    # 这里仅取前几行演示绘图
    x = df.iloc[:, 0]
    y = df.iloc[:, 1]
else:
    # 如果不存在示例 CSV，则使用简单测试数据
    x = [1, 2, 3, 4, 5]
    y = [2, 3, 1, 4, 3]

plt.figure(figsize=(8, 5))
plt.plot(x, y, marker='o')
plt.title('测试中文', fontproperties=font_prop, fontsize=16)
plt.xlabel('横轴标签', fontproperties=font_prop, fontsize=12)
plt.ylabel('纵轴标签', fontproperties=font_prop, fontsize=12)
plt.grid(True)

output_path = "/mnt/f/vs-code-openclaw/font_test.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Saved test plot to: {output_path}")
