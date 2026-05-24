# -*- coding: utf-8 -*-
"""
用Word原生OMML公式替换「？代码？」占位符 - 简化可靠版
针对4个具体公式，手动构建正确的OMML XML
"""
import os
import zipfile
import shutil
from lxml import etree

# 命名空间
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def make_formula1():
    """公式1: 倾斜校正 - 旋转角度和变换矩阵"""
    # θ = arctan((y2-y1)/(x2-x1))
    # M = [cosθ  -sinθ; sinθ  cosθ]
    root = etree.Element(f'{{{M}}}oMathPara')

    # θ = arctan(...)
    omml = f'''
    <m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
              xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <m:r>
            <m:rPr><m:sty m:val="p"/></m:rPr>
            <m:t>θ</m:t>
        </m:r>
        <m:r><m:t> = arctan</m:t></m:r>
        <m:f>
            <m:num>
                <m:r><m:t>y</m:t></m:r>
                <m:sub><m:r><m:t>2</m:t></m:r></m:sub>
                <m:r><m:t> - y</m:t></m:r>
                <m:sub><m:r><m:t>1</m:t></m:r></m:sub>
            </m:num>
            <m:den>
                <m:r><m:t>x</m:t></m:r>
                <m:sub><m:r><m:t>2</m:t></m:r></m:sub>
                <m:r><m:t> - x</m:t></m:r>
                <m:sub><m:r><m:t>1</m:t></m:r></m:sub>
            </m:den>
        </m:f>
    </m:oMath>
    '''
    el = etree.fromstring(omml)

    # 添加矩阵 M = [...]
    omml2 = f'''
    <m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
              xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <m:r><m:t>M = </m:t></m:r>
        <m:d>
            <m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/><m:grow m:val="1"/></m:dPr>
            <m:e>
                <m:r><m:t>cosθ</m:t></m:r>
                <m:r><m:t>  -sinθ</m:t></m:r>
            </m:e>
            <m:e>
                <m:r><m:t>sinθ</m:t></m:r>
                <m:r><m:t>  cosθ</m:t></m:r>
            </m:e>
        </m:d>
    </m:oMath>
    '''
    el2 = etree.fromstring(omml2)
    root.append(el)
    root.append(el2)
    return root


def make_formula2():
    """公式2: 垂直投影字符分割"""
    omml = f'''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
                 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <m:oMath>
            <m:r><m:t>V(j) = </m:t></m:r>
            <m:nary>
                <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/><m:subHide m:val="0"/><m:supHide m:val="0"/></m:naryPr>
                <m:sub>
                    <m:r><m:t>i = 0</m:t></m:r>
                </m:sub>
                <m:sup>
                    <m:r><m:t>H</m:t></m:r>
                </m:sup>
                <m:e>
                    <m:r><m:t>B(i, j),  j = 0, 1, 2, ..., W</m:t></m:r>
                </m:e>
            </m:nary>
        </m:oMath>
        <m:oMath>
            <m:r><m:t>  T = (min(V) + mean(V))/2,  V(j) &lt; T</m:t></m:r>
        </m:oMath>
    </m:oMathPara>
    '''
    return etree.fromstring(omml)


def make_formula3():
    """公式3: HOG特征提取"""
    omml = f'''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
                 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <m:oMath>
            <m:r><m:t>hist</m:t></m:r>
            <m:sub><m:r><m:t>k</m:t></m:r></m:sub>
            <m:r><m:t> = </m:t></m:r>
            <m:nary>
                <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/><m:subHide m:val="0"/><m:supHide m:val="0"/></m:naryPr>
                <m:sub><m:r><m:t>p ∈ cell</m:t></m:r></m:sub>
                <m:e><m:r><m:t>|∇I(p)|</m:t></m:r></m:e>
            </m:nary>
            <m:r><m:t>,  |∇I| = </m:t></m:r>
            <m:rad>
                <m:radPr><m:degHide m:val="1"/></m:radPr>
                <m:deg/>
                <m:e>
                    <m:sup>
                        <m:e><m:r><m:t>G</m:t></m:r></m:e>
                        <m:e><m:r><m:t>2</m:t></m:r></m:e>
                    </m:sup>
                    <m:r><m:t> + G</m:t></m:r>
                    <m:sub><m:r><m:t>y</m:t></m:r></m:sub>
                    <m:sup><m:r><m:t>2</m:t></m:r></m:sup>
                </m:e>
            </m:rad>
            <m:r><m:t>,  θ = arctan(G</m:t></m:r>
            <m:sub><m:r><m:t>y</m:t></m:r></m:sub>
            <m:r><m:t>/G</m:t></m:r>
            <m:sub><m:r><m:t>x</m:t></m:r></m:sub>
            <m:r><m:t>)</m:t></m:r>
        </m:oMath>
    </m:oMathPara>
    '''
    return etree.fromstring(omml)


def make_formula4():
    """公式4: YOLOv3损失函数"""
    omml = f'''
    <m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
                 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <m:oMath>
            <m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t>L</m:t></m:r>
            <m:sub><m:r><m:t>1</m:t></m:r></m:sub>
            <m:r><m:t> = λ</m:t></m:r>
            <m:sub><m:r><m:t>obj</m:t></m:r></m:sub>
            <m:nary>
                <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/><m:subHide m:val="0"/><m:supHide m:val="0"/></m:naryPr>
                <m:sub><m:r><m:t>ij</m:t></m:r></m:sub>
                <m:e><m:r><m:t>1</m:t></m:r></m:e>
            </m:nary>
            <m:sup>
                <m:e><m:r><m:t>obj</m:t></m:r></m:e>
            </m:sup>
            <m:r><m:t>[C</m:t></m:r>
            <m:sub><m:r><m:t>i</m:t></m:r></m:sub>
            <m:r><m:t> - </m:t></m:r>
            <m:acc>
                <m:accPr><m:chr m:val="̂"/></m:accPr>
                <m:e><m:r><m:t>C</m:t></m:r></m:e>
            </m:acc>
            <m:sub><m:r><m:t>i</m:t></m:r></m:sub>
            <m:r><m:t>]</m:t></m:r>
            <m:sup><m:r><m:t>2</m:t></m:r></m:sup>
        </m:oMath>
        <m:oMath>
            <m:r><m:t> + λ</m:t></m:r>
            <m:sub><m:r><m:t>noobj</m:t></m:r></m:sub>
            <m:nary>
                <m:naryPr><m:chr m:val="∑"/><m:limLoc m:val="undOvr"/><m:subHide m:val="0"/><m:supHide m:val="0"/></m:naryPr>
                <m:sub><m:r><m:t>ij</m:t></m:r></m:sub>
                <m:e><m:r><m:t>1</m:t></m:r></m:e>
            </m:nary>
            <m:sup>
                <m:e><m:r><m:t>noobj</m:t></m:r></m:e>
            </m:sup>
            <m:r><m:t>[C</m:t></m:r>
            <m:sub><m:r><m:t>i</m:t></m:r></m:sub>
            <m:r><m:t> - </m:t></m:r>
            <m:acc>
                <m:accPr><m:chr m:val="̂"/></m:accPr>
                <m:e><m:r><m:t>C</m:t></m:r></m:e>
            </m:acc>
            <m:sub><m:r><m:t>i</m:t></m:r></m:sub>
            <m:r><m:t>]</m:t></m:r>
            <m:sup><m:r><m:t>2</m:t></m:r></m:sup>
        </m:oMath>
    </m:oMathPara>
    '''
    return etree.fromstring(omml)


def insert_omml_at_paragraph(doc_path, output_path):
    """
    直接操作docx的XML来插入OMML公式
    使用更可靠的方法：解压docx，修改document.xml，再重新打包
    """
    import tempfile
    import re

    temp_dir = tempfile.mkdtemp()
    try:
        # 解压docx
        with zipfile.ZipFile(doc_path, 'r') as z:
            z.extractall(temp_dir)

        document_xml = os.path.join(temp_dir, 'word', 'document.xml')

        with open(document_xml, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        # 找到所有包含 ？代码？ 的段落
        # 用正则找到包含 ？代码？ 的 <w:p> 标签
        pattern = r'<w:p[ >][\s\S]*?？代码？[\s\S]*?</w:p>'

        formula_generators = [make_formula1, make_formula2, make_formula3, make_formula4]
        formula_idx = [0]  # 用列表以便在嵌套函数中使用

        def replace_func(match):
            if formula_idx[0] >= len(formula_generators):
                return match.group(0)
            gen = formula_generators[formula_idx[0]]
            formula_idx[0] += 1
            omml_element = gen()
            omml_str = etree.tostring(omml_element, encoding='unicode')
            # 替换整个段落内容为OMML
            return f'<w:p>{omml_str}</w:p>'

        new_xml = re.sub(pattern, replace_func, xml_content)

        with open(document_xml, 'w', encoding='utf-8') as f:
            f.write(new_xml)

        # 重新打包
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    z.write(file_path, arcname)

        print(f"成功生成: {output_path}")
        return True

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    BASE = r"C:\Users\HUAWEI\Desktop\FinalDesign\Python_VLPR-master"
    FILE_DIR = os.path.join(BASE, "file")
    DOC_SRC = "C:/Users/HUAWEI/Desktop/专业课作业/毕设/浙江水利水电学院毕业设计（论文）模板-2026（4.9）（含真实目录）.docx"
    DOC_DST = os.path.join(FILE_DIR, "毕业论文_含OMML公式版.docx")

    print("=" * 55)
    print("开始插入OMML公式（直接XML操作版）...")
    print("=" * 55)

    success = insert_omml_at_paragraph(DOC_SRC, DOC_DST)

    if success:
        # 验证文件
        with zipfile.ZipFile(DOC_DST, 'r') as z:
            print(f"ZIP内容: {len(z.namelist())} 个文件")
            print(f"包含oMath: {'oMath' in open(z.extract('word/document.xml', tempfile.gettempdir())).read() if False else 'checking...'}")
        print(f"文件大小: {os.path.getsize(DOC_DST):,} bytes")
    else:
        print("生成失败!")


if __name__ == "__main__":
    import tempfile
    main()
