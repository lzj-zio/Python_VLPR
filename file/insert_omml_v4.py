# -*- coding: utf-8 -*-
"""
用Word原生OMML公式替换「？代码？」占位符 - 修正版
关键修复：OMML中的文本使用<m:t>而非<w:t>
"""
import os
import zipfile
import shutil
import tempfile
from lxml import etree

# 命名空间
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def make_formula_element(formula_num):
    """根据公式编号返回正确的OMML元素"""
    nsmap = {'m': M_NS, 'w': W_NS}
    
    if formula_num == 1:
        return _build_formula1(nsmap)
    elif formula_num == 2:
        return _build_formula2(nsmap)
    elif formula_num == 3:
        return _build_formula3(nsmap)
    elif formula_num == 4:
        return _build_formula4(nsmap)
    return None


def _m(tag):
    """返回带m命名空间的元素标签"""
    return f'{{{M_NS}}}{tag}'


def _w(tag):
    """返回带w命名空间的元素标签"""
    return f'{{{W_NS}}}{tag}'


def _add_math_text(parent, text):
    """在OMML元素中添加数学文本（使用<m:t>）"""
    r = etree.SubElement(parent, _m('r'))
    t = etree.SubElement(r, _m('t'))
    t.text = text
    return r


def _add_math_text_with_style(parent, text, style='p'):
    """添加带样式的数学文本（style: p=普通, b=粗体, i=斜体等）"""
    r = etree.SubElement(parent, _m('r'))
    rPr = etree.SubElement(r, _m('rPr'))
    sty = etree.SubElement(rPr, _m('sty'))
    sty.set(_m('val'), style)
    t = etree.SubElement(r, _m('t'))
    t.text = text
    return r


def _build_formula1(nsmap):
    """公式1: θ = arctan((y2-y1)/(x2-x1)), M = (cosθ -sinθ; sinθ cosθ)"""
    oMathPara = etree.Element(_m('oMathPara'), nsmap=nsmap)
    
    # 第一个oMath: θ = arctan(...)
    oMath1 = etree.SubElement(oMathPara, _m('oMath'))
    
    # θ =
    _add_math_text_with_style(oMath1, 'θ', 'p')
    _add_math_text(oMath1, ' = arctan')
    
    # 分式 (y2-y1)/(x2-x1)
    f = etree.SubElement(oMath1, _m('f'))
    fPr = etree.SubElement(f, _m('fPr'))
    ctrlPr = etree.SubElement(fPr, _m('ctrlPr'))
    
    num = etree.SubElement(f, _m('num'))
    _add_math_text(num, 'y')
    _add_sub(num, '2')
    _add_math_text(num, ' - y')
    _add_sub(num, '1')
    
    den = etree.SubElement(f, _m('den'))
    _add_math_text(den, 'x')
    _add_sub(den, '2')
    _add_math_text(den, ' - x')
    _add_sub(den, '1')
    
    # 第二个oMath: M = (cosθ  -sinθ; sinθ  cosθ)
    oMath2 = etree.SubElement(oMathPara, _m('oMath'))
    _add_math_text(oMath2, 'M = ')
    
    # 括号矩阵
    d = etree.SubElement(oMath2, _m('d'))
    dPr = etree.SubElement(d, _m('dPr'))
    begChr = etree.SubElement(dPr, _m('begChr'))
    begChr.set(_m('val'), '(')
    endChr = etree.SubElement(dPr, _m('endChr'))
    endChr.set(_m('val'), ')')
    
    # 第一行: cosθ  -sinθ
    e1 = etree.SubElement(d, _m('e'))
    _add_math_text(e1, 'cosθ  -sinθ')
    
    # 第二行: sinθ  cosθ
    e2 = etree.SubElement(d, _m('e'))
    _add_math_text(e2, 'sinθ  cosθ')
    
    return oMathPara


def _add_sub(parent, text):
    """添加下标"""
    sub = etree.SubElement(parent, _m('sub'))
    r = etree.SubElement(sub, _m('r'))
    t = etree.SubElement(r, _m('t'))
    t.text = text


def _add_sup(parent, text):
    """添加上标"""
    sup = etree.SubElement(parent, _m('sup'))
    r = etree.SubElement(sup, _m('r'))
    t = etree.SubElement(r, _m('t'))
    t.text = text


def _build_formula2(nsmap):
    """公式2: V(j) = ΣB(i,j), T = (min+mean)/2, V(j) < T"""
    oMathPara = etree.Element(_m('oMathPara'), nsmap=nsmap)
    
    oMath = etree.SubElement(oMathPara, _m('oMath'))
    _add_math_text(oMath, 'V(j) = ')
    
    # 累加符号 Σ
    nary = etree.SubElement(oMath, _m('nary'))
    naryPr = etree.SubElement(nary, _m('naryPr'))
    chr_el = etree.SubElement(naryPr, _m('chr'))
    chr_el.set(_m('val'), '∑')
    limLoc = etree.SubElement(naryPr, _m('limLoc'))
    limLoc.set(_m('val'), 'undOvr')
    
    sub = etree.SubElement(nary, _m('sub'))
    _add_math_text(sub, 'i = 0')
    sup = etree.SubElement(nary, _m('sup'))
    _add_math_text(sup, 'H')
    e = etree.SubElement(nary, _m('e'))
    _add_math_text(e, 'B(i, j),  j = 0, 1, 2, ..., W')
    
    # 第二部分
    oMath2 = etree.SubElement(oMathPara, _m('oMath'))
    _add_math_text(oMath2, '  T = (min(V) + mean(V))/2,  V(j) < T')
    
    return oMathPara


def _build_formula3(nsmap):
    """公式3: HOG特征提取"""
    oMathPara = etree.Element(_m('oMathPara'), nsmap=nsmap)
    
    oMath = etree.SubElement(oMathPara, _m('oMath'))
    _add_math_text(oMath, 'hist')
    _add_sub(oMath, 'k')
    _add_math_text(oMath, ' = ')
    
    # 累加 Σ
    nary = etree.SubElement(oMath, _m('nary'))
    naryPr = etree.SubElement(nary, _m('naryPr'))
    chr_el = etree.SubElement(naryPr, _m('chr'))
    chr_el.set(_m('val'), '∑')
    
    sub = etree.SubElement(nary, _m('sub'))
    _add_math_text(sub, 'p∈cell')
    _add_sub(sub, 'k')
    e = etree.SubElement(nary, _m('e'))
    _add_math_text(e, '|∇I(p)|')
    
    _add_math_text(oMath, ',  |∇I| = ')
    
    # 根号
    rad = etree.SubElement(oMath, _m('rad'))
    radPr = etree.SubElement(rad, _m('radPr'))
    degHide = etree.SubElement(radPr, _m('degHide'))
    degHide.set(_m('val'), '1')
    deg = etree.SubElement(rad, _m('deg'))
    e_rad = etree.SubElement(rad, _m('e'))
    _add_math_text(e_rad, 'G')
    _add_sup(e_rad, '2')
    _add_math_text(e_rad, ' + G')
    _add_sub(e_rad, 'y')
    _add_sup(e_rad, '2')
    
    _add_math_text(oMath, ',  θ = arctan(G')
    _add_sub(oMath, 'y')
    _add_math_text(oMath, '/G')
    _add_sub(oMath, 'x')
    _add_math_text(oMath, ')')
    
    return oMathPara


def _build_formula4(nsmap):
    """公式4: YOLOv3损失函数"""
    oMathPara = etree.Element(_m('oMathPara'), nsmap=nsmap)
    
    # L1 = λ_obj Σ ...
    oMath1 = etree.SubElement(oMathPara, _m('oMath'))
    _add_math_text_with_style(oMath1, 'L', 'p')
    _add_sub(oMath1, '1')
    _add_math_text(oMath1, ' = λ')
    _add_sub(oMath1, 'obj')
    _add_math_text(oMath1, '∑')
    _add_sub(oMath1, 'ij')
    _add_sup(oMath1, 'obj')
    _add_math_text(oMath1, '[C')
    _add_sub(oMath1, 'i')
    _add_math_text(oMath1, ' - Ĉ')
    _add_sub(oMath1, 'i')
    _add_math_text(oMath1, ']')
    _add_sup(oMath1, '2')
    
    # + λ_noobj Σ ...
    oMath2 = etree.SubElement(oMathPara, _m('oMath'))
    _add_math_text(oMath2, ' + λ')
    _add_sub(oMath2, 'noobj')
    _add_math_text(oMath2, '∑')
    _add_sub(oMath2, 'ij')
    _add_sup(oMath2, 'noobj')
    _add_math_text(oMath2, '[C')
    _add_sub(oMath2, 'i')
    _add_math_text(oMath2, ' - Ĉ')
    _add_sub(oMath2, 'i')
    _add_math_text(oMath2, ']')
    _add_sup(oMath2, '2')
    
    return oMathPara


def insert_formulas(docx_path, output_path):
    """解压docx，找到？代码？占位符并替换为OMML公式"""
    temp_dir = tempfile.mkdtemp()
    try:
        # 解压
        with zipfile.ZipFile(docx_path, 'r') as z:
            z.extractall(temp_dir)
        
        document_path = os.path.join(temp_dir, 'word', 'document.xml')
        
        # 用lxml解析
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(document_path, parser)
        root = tree.getroot()
        
        formula_idx = [0]  # 闭包变量
        
        # 找到所有段落
        paragraphs = root.findall('.//{' + W_NS + '}p')
        
        for para in paragraphs:
            text = ''.join(t.text or '' for t in para.iter('{' + W_NS + '}t'))
            if '？代码？' in text:
                if formula_idx[0] < 4:
                    # 清空段落内容
                    for child in list(para):
                        para.remove(child)
                    
                    # 添加OMML公式元素
                    formula_el = make_formula_element(formula_idx[0] + 1)
                    if formula_el is not None:
                        para.append(formula_el)
                    
                    formula_idx[0] += 1
                    print(f"已替换公式 {formula_idx[0]}")
        
        # 保存修改后的XML (使用正确的XML声明格式)
        tree.write(document_path, xml_declaration=True, encoding='UTF-8', standalone='yes')
        
        # 重新打包
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for root_dir, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    z.write(file_path, arcname)
        
        print(f"\n成功！已生成: {output_path}")
        print(f"文件大小: {os.path.getsize(output_path):,} bytes")
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
    print("生成OMML公式版文档（修正版 - 使用<m:t>）")
    print("=" * 55)

    if not os.path.exists(DOC_SRC):
        print(f"源文件不存在: {DOC_SRC}")
        return

    insert_formulas(DOC_SRC, DOC_DST)


if __name__ == "__main__":
    main()
