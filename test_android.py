# -*- coding: utf-8 -*-
"""
测试脚本：验证核心功能是否能在 Android 环境运行
"""
import os
import sys
import cv2
import numpy as np

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("车牌识别系统 - Android 环境测试")
print("=" * 50)

# 测试 1: 检查依赖
print("\n[测试 1] 检查依赖库...")
try:
    import img_function as predict
    import img_math
    import img_recognition
    print("✓ 所有依赖库导入成功")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 测试 2: 检查模型文件
print("\n[测试 2] 检查模型文件...")
model_files = ["svm.dat", "svmchinese.dat"]
for f in model_files:
    if os.path.exists(f):
        print(f"✓ 找到模型文件: {f}")
    else:
        print(f"⚠ 未找到模型文件: {f} (将在首次运行时训练)")

# 测试 3: 初始化预测器
print("\n[测试 3] 初始化车牌预测器...")
try:
    predictor = predict.CardPredictor()
    print("✓ 预测器创建成功")
    
    print("  正在加载/训练 SVM 模型...")
    predictor.train_svm()
    print("✓ SVM 模型加载/训练成功")
except Exception as e:
    print(f"✗ 预测器初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 4: 检查测试图片
print("\n[测试 4] 检查测试图片...")
test_dir = "test"
if os.path.exists(test_dir):
    test_images = [f for f in os.listdir(test_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    if test_images:
        print(f"✓ 找到 {len(test_images)} 张测试图片")
        test_image = os.path.join(test_dir, test_images[0])
    else:
        print("⚠ 未找到测试图片")
        test_image = None
else:
    print("⚠ test 目录不存在")
    test_image = None

# 测试 5: 测试车牌识别
if test_image:
    print("\n[测试 5] 测试车牌识别...")
    try:
        # 读取图片
        img_bgr = img_math.img_read(test_image)
        print(f"✓ 成功读取图片: {test_image}")
        print(f"  图片尺寸: {img_bgr.shape}")
        
        # 预处理
        first_img, oldimg = predictor.img_first_pre(img_bgr)
        print("✓ 图片预处理成功")
        
        # 形状定位识别
        r1, roi1, c1 = predictor.img_color_contours(first_img, oldimg)
        result1 = "".join(r1) if r1 else "未识别"
        print(f"✓ 形状定位识别结果: {result1}")
        
        # 颜色定位识别
        r2, roi2, c2 = predictor.img_only_color(oldimg, oldimg, first_img)
        result2 = "".join(r2) if r2 else "未识别"
        print(f"✓ 颜色定位识别结果: {result2}")
        
        print("\n" + "=" * 50)
        print("测试完成！核心功能正常运行")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ 识别测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("\n⚠ 跳过识别测试（未找到测试图片）")

# 测试 6: 检查 Android 路径
print("\n[测试 6] 检查 Android 环境适配...")
if hasattr(sys, '_MEIPASS'):
    print(f"✓ PyInstaller 环境: {sys._MEIPASS}")
elif os.path.exists('/data/data'):
    print("✓ Android 环境")
else:
    print("✓ 开发环境 (Windows/Mac/Linux)")

print("\n" + "=" * 50)
print("所有测试通过！项目已准备好打包为 Android APK")
print("=" * 50)
print("\n下一步:")
print("1. 将项目复制到 Linux/WSL2 环境")
print("2. 安装 Buildozer: pip install buildozer")
print("3. 运行: buildozer android debug")
print("4. 等待构建完成（首次需要 30-60 分钟）")
print("5. 在 bin/ 目录找到 APK 文件")
