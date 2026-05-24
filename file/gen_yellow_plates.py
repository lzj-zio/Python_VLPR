# -*- coding: utf-8 -*-
"""
生成工程车黄色车牌测试图片
- 黄底黑字标准格式（省份+字母+5位字母数字）
- 模拟真实车辆尾部拍摄场景（带车身背景、铆钉、边框）
- 加入随机扰动：轻微倾斜/模糊/亮度变化/噪声
- 输出到 img/ 目录，供 Python_VLPR 项目识别测试
"""

import os
import random
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

OUTPUT_DIR = r"C:\Users\HUAWEI\Desktop\FinalDesign\Python_VLPR-master\img"
FONT_CN = "C:/Windows/Fonts/simhei.ttf"   # 中文黑体
FONT_EN = "C:/Windows/Fonts/simhei.ttf"    # 英文数字也用黑体（清晰）

# 省份简称（常用工程车归属地）
PROVINCES = ["鲁", "豫", "冀", "苏", "浙", "粤", "皖", "赣",
             "鄂", "湘", "川", "陕", "晋", "辽", "吉", "黑"]
# 字母
LETTERS = list("ABCDEFGHJKLMNPQRSTUVWXYZ")
# 字母+数字
ALPHANUM = list("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789")


def generate_plate_text():
    """生成随机车牌号"""
    prov = random.choice(PROVINCES)
    city = random.choice(LETTERS)
    rest = "".join(random.choice(ALPHANUM) for _ in range(5))
    return f"{prov}{city}{rest}"


def draw_plate_image(text, width=440, height=140):
    """
    绘制纯车牌图像（黄底黑字，含边框和铆钉）
    返回 RGBA 图像对象
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 车牌底色：亮黄色 (#FCD116 标准黄牌色)
    plate_color = (252, 209, 22, 255)  # 黄色
    draw.rectangle([2, 2, width - 3, height - 3], fill=plate_color)

    # 黑色边框
    border_color = (30, 30, 30, 255)
    draw.rectangle([0, 0, width - 1, height - 1], outline=border_color, width=2)

    # 铆钉（4个角各一个，灰色小圆点）
    rivet_color = (120, 120, 120, 255)
    rivet_r = 4
    margin = 10
    for x in [margin, width - margin]:
        for y in [margin, height - margin]:
            draw.ellipse([x - rivet_r, y - rivet_r, x + rivet_r, y + rivet_r], fill=rivet_color)

    # 分隔符（第二个字符后的小圆点，部分黄牌有）
    sep_x = int(width * 0.235)
    sep_y = height // 2
    dot_r = 3
    draw.ellipse([sep_x - dot_r, sep_y - dot_r, sep_x + dot_r, sep_y + dot_r], fill=(0, 0, 0, 255))

    # 绘制字符
    char_color = (0, 0, 0, 255)  # 黑色文字
    font_size_cn = int(height * 0.58)   # 中文字号
    font_size_en = int(height * 0.55)   # 字母数字字号

    try:
        font_cn = ImageFont.truetype(FONT_CN, font_size_cn)
        font_en = ImageFont.truetype(FONT_EN, font_size_en)
    except OSError:
        font_cn = ImageFont.load_default()
        font_en = font_cn

    # 计算字符位置：均匀分布
    n = len(text)  # 7 个字符
    # 起始X偏移（左侧留空给省名），每个字符间距
    start_x = int(width * 0.06)
    total_w = int(width * 0.82)
    char_spacing = total_w // n

    for i, ch in enumerate(text):
        if i == 0:
            font = font_cn
        else:
            font = font_en

        # 居中绘制
        bbox = draw.textbbox((0, 0), ch, font=font)
        cw = bbox[2] - bbox[0]
        ch_h = bbox[3] - bbox[1]

        cx = start_x + i * char_spacing + (char_spacing - cw) // 2
        cy = (height - ch_h) // 2 - 2

        draw.text((cx, cy), ch, fill=char_color, font=font)

    return img


def add_vehicle_background(plate_img, bg_type="truck"):
    """
    将车牌贴到模拟的车辆尾部背景上，使照片看起来像真实拍摄的
    bg_type: truck | excavator | concrete | mixer
    """
    pw, ph = plate_img.size
    # 背景尺寸约为车牌的 3~4 倍
    bg_w = pw * random.randint(4, 5)
    bg_h = ph * random.randint(4, 6)

    if bg_type == "truck":
        base_color = (
            random.randint(200, 240),
            random.randint(205, 245),
            random.randint(210, 250),
            255,
        )  # 白/灰车尾
    elif bg_type == "excavator":
        base_color = (
            random.randint(210, 230),
            random.randint(180, 210),
            random.randint(140, 180),
            255,
        )  # 黄色挖掘机
    elif bg_type == "concrete":
        base_color = (
            random.randint(180, 220),
            random.randint(190, 225),
            random.randint(195, 230),
            255,
        )  # 灰白搅拌车
    else:  # mixer / dump
        base_color = (
            random.randint(160, 210),
            random.randint(175, 215),
            random.randint(185, 225),
            255,
        )

    background = Image.new("RGBA", (bg_w, bg_h), base_color)
    bg_draw = ImageDraw.Draw(background)

    # 添加一些纹理线条（模拟金属板接缝/漆面纹理）
    for _ in range(random.randint(3, 8)):
        y = random.randint(0, bg_h)
        shade = random.randint(-15, 15)
        c = tuple(max(0, min(255, base_color[i] + shade)) for i in range(3)) + (255,)
        bg_draw.line([(0, y), (bg_w, y)], fill=c, width=1)

    # 模拟尾灯或反光条（可选）
    if random.random() > 0.5:
        ly = random.choice([ph // 2, bg_h - ph // 2])
        lx = random.choice([pw // 4, bg_w - pw // 4])
        light_color = (255, 60, 20, 200)
        bg_draw.rounded_rectangle(
            [lx, ly, lx + pw // 3, ly + ph // 3],
            radius=5,
            fill=light_color,
        )

    # 将车牌粘贴到背景中央偏下位置
    paste_x = (bg_w - pw) // 2 + random.randint(-pw // 10, pw // 10)
    paste_y = (bg_h - ph) // 2 + random.randint(ph // 4, ph)

    # 创建带圆角的遮罩让车牌更自然
    mask = Image.new("L", (pw, ph), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([2, 2, pw - 3, ph - 3], radius=4, fill=255)

    background.paste(plate_img, (paste_x, paste_y), mask)

    return background.convert("RGB")


def apply_realistic_effects(img):
    """
    添加真实拍照效果：
    - 轻微高斯模糊（模拟对焦不完全锐利）
    - 随机亮度/对比度调整
    - 轻微噪声（模拟传感器噪点）
    - 可选的轻微旋转（模拟拍摄角度）
    """
    # 随机亮度调整 ±20%
    brightness_factor = random.uniform(0.85, 1.15)
    img = ImageEnhance.Brightness(img).enhance(brightness_factor)

    # 对比度调整
    contrast_factor = random.uniform(0.9, 1.15)
    img = ImageEnhance.Contrast(img).enhance(contrast_factor)

    # 色彩饱和度微调
    color_factor = random.uniform(0.85, 1.15)
    img = ImageEnhance.Color(img).enhance(color_factor)

    # 轻微模糊（模拟镜头非完美对焦）
    if random.random() > 0.35:
        radius = random.choice([0, 0, 0, 0, 1])  # 大多数保持清晰
        if radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=radius))

    # 转numpy加噪声再转回
    arr = np.array(img, dtype=np.float32)
    noise_level = random.uniform(0, 6)  # 噪声强度
    noise = np.random.normal(0, noise_level, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    # 轻微旋转（-5° 到 +5°）
    angle = random.uniform(-5, 5)
    if abs(angle) > 0.5:
        img = img.rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=tuple(
            int(np.mean(np.array(img)[i])) for i in range(3)))

    return img


def resize_to_standard(img, max_width=None):
    """缩放到合理尺寸（类似手机拍摄）"""
    w, h = img.size
    if max_width and w > max_width:
        ratio = max_width / w
        new_size = (max_width, int(h * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    return img


def generate_one(index, seed=None):
    """生成一张黄色工程车牌图片"""
    if seed is not None:
        random.seed(seed)

    text = generate_plate_text()
    print(f"  [{index}] 生成车牌: {text}")

    # 1. 绘制车牌
    plate = draw_plate_image(text)

    # 2. 添加车辆背景
    bg_type = random.choice(["truck", "truck", "excavator", "concrete", "mixer"])
    scene = add_vehicle_background(plate, bg_type)

    # 3. 应用真实效果
    result = apply_realistic_effects(scene)

    # 4. 缩放到合适大小
    result = resize_to_standard(result, max_width=random.choice([800, 1000, 1280]))

    return result, text


def main():
    print("=" * 50)
    print("  工程车黄色车牌测试图片生成器")
    print("=" * 50)

    count = 12  # 生成数量
    outputs = []

    for i in range(count):
        img, text = generate_one(i + 1, seed=42 + i * 17)

        filename = f"yellow_plate_{i + 1:02d}_{text}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath, "JPEG", quality=95)
        outputs.append((filepath, text, img.size))
        print(f"      -> 已保存: {filename} ({img.size[0]}x{img.size[1]})")

    print()
    print(f"\n{'='*50}")
    print(f"  完成！共生成 {count} 张黄色工程车牌图片")
    print(f"  保存目录: {OUTPUT_DIR}")
    print(f"{'='*50}")
    print(f"\n文件列表:")
    for fp, text, size in outputs:
        fn = os.path.basename(fp)
        print(f"  - {fn}  ({size[0]}x{size[1]})  车牌号: {text}")


if __name__ == "__main__":
    main()
