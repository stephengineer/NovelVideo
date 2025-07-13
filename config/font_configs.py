"""
字体配置文件
定义所有可用的字体样式配置
"""

from pathlib import Path

# 字体配置类：存储单个字体的所有参数
class FontConfig:
    def __init__(self, name, font_path, max_chars, font_size, font_color, stroke_color, stroke_width=2):
        self.name = name                    # 字体配置名称
        self.font_path = font_path          # 字体文件路径
        self.max_chars = max_chars          # 该字体对应的最大每行字符数
        self.font_size = font_size          # 字体大小
        self.font_color = font_color        # 字体颜色（如"yellow"）
        self.stroke_color = stroke_color    # 描边颜色（如"black"）
        self.stroke_width = stroke_width    # 描边宽度（默认2像素）

# 字体文件路径
FONT_BASE_PATH = Path(__file__).parent.parent / "assets" / "fonts"

# 所有可用的字体配置
FONT_CONFIGS = [
    # 配置1：黄色字体+黑色描边，适合较宽字体
    FontConfig(
        name="yellow_black",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=10,
        font_size=50,
        font_color="yellow",
        stroke_color="black",
        stroke_width=2
    ),
    
    # 配置2：白色字体+黄色描边，适合较窄字体
    FontConfig(
        name="white_yellow",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="white",
        stroke_color="yellow",
        stroke_width=3
    ),
    
    # 配置3：红色字体+白色描边
    FontConfig(
        name="red_white",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="red",
        stroke_color="white",
        stroke_width=2
    ),
    
    # 配置4：白色字体+黑色描边，经典搭配
    FontConfig(
        name="white_black",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="white",
        stroke_color="black",
        stroke_width=2
    ),
    
    # 配置5：金色字体+深蓝描边，高端感
    FontConfig(
        name="gold_blue",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="#FFD700",  # 金色
        stroke_color="#000080",  # 深蓝色
        stroke_width=3
    ),
    
    # 配置6：青色字体+黑色描边，清新感
    FontConfig(
        name="cyan_black",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="#00FFFF",  # 青色
        stroke_color="black",
        stroke_width=2
    ),
    
    # 配置7：橙色字体+白色描边，温暖感
    FontConfig(
        name="orange_white",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="#FFA500",  # 橙色
        stroke_color="white",
        stroke_width=2
    ),
    
    # 配置8：绿色字体+黑色描边，自然感
    FontConfig(
        name="green_black",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="#32CD32",  # 绿色
        stroke_color="black",
        stroke_width=2
    ),
    
    # 配置9：紫色字体+白色描边，神秘感
    FontConfig(
        name="purple_white",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="#800080",  # 紫色
        stroke_color="white",
        stroke_width=3
    ),
    
    # 配置10：粉色字体+深灰描边，温馨感
    FontConfig(
        name="pink_gray",
        font_path=str(FONT_BASE_PATH / "NotoSansSC-Regular.ttf"),
        max_chars=8,
        font_size=70,
        font_color="#FFC0CB",  # 粉色
        stroke_color="#404040",  # 深灰色
        stroke_width=2
    )
]

def get_font_config_by_name(name: str) -> FontConfig:
    """根据名称获取字体配置"""
    for config in FONT_CONFIGS:
        if config.name == name:
            return config
    # 如果找不到指定名称，返回默认配置
    return FONT_CONFIGS[0]

def get_random_font_config() -> FontConfig:
    """随机获取一个字体配置"""
    import random
    return random.choice(FONT_CONFIGS)

def get_font_config_names() -> list:
    """获取所有字体配置名称"""
    return [config.name for config in FONT_CONFIGS] 