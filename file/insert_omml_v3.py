# -*- coding: utf-8 -*-
"""
用Word原生OMML公式替换「？代码？」占位符 - XML直接操作版
直接解压docx，用lxml解析document.xml，正确插入OMML公式后重新打包
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
    """
    根据公式编号，返回对应的OMML XML元素（作为段落的子元素）
    返回一个 etree.Element 列表，可以直接插入到 <w:p> 中
    """
    if formula_num == 1:
        return _build_formula1()
    elif formula_num == 2:
        return _build_formula2()
    elif formula_num == 3:
        return _build_formula3()
    elif formula_num == 4:
        return _build_formula4()
    return []


def _build_formula1():
    """公式1: θ = arctan((y2-y1)/(x2-x1)), M = (cosθ -sinθ; sinθ cosθ)"""
    nsmap = {'m': M_NS, 'w': W_NS}
    
    # 创建 oMathPara 包装
    oMathPara = etree.Element(f'{{{M_NS}}}oMathPara', nsmap=nsmap)
    
    # 第一个oMath: θ = arctan(...)
    oMath1 = etree.SubElement(oMathPara, f'{{{M_NS}}}oMath')
    
    # θ =
    r1 = etree.SubElement(oMath1, f'{{{M_NS}}}r')
    rPr1 = etree.SubElement(r1, f'{{{M_NS}}}rPr')
    sty1 = etree.SubElement(rPr1, f'{{{M_NS}}}sty')
    sty1.set(f'{{{M_NS}}}val', 'p')
    t1 = etree.SubElement(r1, f'{{{W_NS}}}t')
    t1.text = 'θ'
    
    r2 = etree.SubElement(oMath1, f'{{{M_NS}}}r')
    t2 = etree.SubElement(r2, f'{{{W_NS}}}t')
    t2.text = ' = arctan'
    
    # 分式
    f = etree.SubElement(oMath1, f'{{{M_NS}}}f')
    fPr = etree.SubElement(f, f'{{{M_NS}}}fPr')
    ctrlPr = etree.SubElement(fPr, f'{{{M_NS}}}ctrlPr')
    rFonts = etree.SubElement(ctrlPr, f'{{{W_NS}}}rFonts')
    rFonts.set(f'{{{W_NS}}}ascii', 'Cambria Math')
    
    num = etree.SubElement(f, f'{{{M_NS}}}num')
    _add_text(num, 'y')
    _add_sub(num, '2')
    _add_text(num, ' - y')
    _add_sub(num, '1')
    
    den = etree.SubElement(f, f'{{{M_NS}}}den')
    _add_text(den, 'x')
    _add_sub(den, '2')
    _add_text(den, ' - x')
    _add_sub(den, '1')
    
    # 第二个oMath: M = (cosθ  -sinθ; sinθ  cosθ)
    oMath2 = etree.SubElement(oMathPara, f'{{{M_NS}}}oMath')
    _add_text(oMath2, 'M = ')
    
    # 矩阵用括号包装
    d = etree.SubElement(oMath2, f'{{{M_NS}}}d')
    dPr = etree.SubElement(d, f'{{{M_NS}}}dPr')
    begChr = etree.SubElement(dPr, f'{{{M_NS}}}begChr')
    begChr.set(f'{{{M_NS}}}val', '(')
    endChr = etree.SubElement(dPr, f'{{{M_NS}}}endChr')
    endChr.set(f'{{{M_NS}}}val', ')')
    
    # 第一行
    e1 = etree.SubElement(d, f'{{{M_NS}}}e')
    _add_text(e1, 'cosθ')
    r_space = etree.SubElement(e1, f'{{{M_NS}}}r')
    t_space = etree.SubElement(r_space, f'{{{W_NS}}}t')
    t_space.text = '  '
    _add_text(e1, '-sinθ')
    
    # 第二行
    e2 = etree.SubElement(d, f'{{{M_NS}}}e')
    _add_text(e2, 'sinθ')
    r_space2 = etree.SubElement(e2, f'{{{M_NS}}}r')
    t_space2 = etree.SubElement(r_space2, f'{{{W_NS}}}t')
    t_space2.text = '  '
    _add_text(e2, 'cosθ')
    
    return [oMathPara]


def _build_formula2():
    """公式2: V(j) = ΣB(i,j), T = (min+mean)/2, V(j) < T"""
    nsmap = {'m': M_NS, 'w': W_NS}
    oMathPara = etree.Element(f'{{{M_NS}}}oMathPara', nsmap=nsmap)
    
    oMath = etree.SubElement(oMathPara, f'{{{M_NS}}}oMath')
    _add_text(oMath, 'V(j) = ')
    
    # 累加符号
    nary = etree.SubElement(oMath, f'{{{M_NS}}}nary')
    naryPr = etree.SubElement(nary, f'{{{M_NS}}}naryPr')
    chr_el = etree.SubElement(naryPr, f'{{{M_NS}}}chr')
    chr_el.set(f'{{{M_NS}}}val', '∑')
    limLoc = etree.SubElement(naryPr, f'{{{M_NS}}}limLoc')
    limLoc.set(f'{{{M_NS}}}val', 'undOvr')
    
    sub = etree.SubElement(nary, f'{{{M_NS}}}sub')
    _add_text(sub, 'i = 0')
    sup = etree.SubElement(nary, f'{{{M_NS}}}sup')
    _add_text(sup, 'H')
    e = etree.SubElement(nary, f'{{{M_NS}}}e')
    _add_text(e, 'B(i, j),  j = 0, 1, 2, ..., W')
    
    # 第二部分
    oMath2 = etree.SubElement(oMathPara, f'{{{M_NS}}}oMath')
    _add_text(oMath2, '  T = (min(V) + mean(V))/2,  V(j) < T')
    
    return [oMathPara]


def _build_formula3():
    """公式3: HOG特征提取"""
    nsmap = {'m': M_NS, 'w': W_NS}
    oMathPara = etree.Element(f'{{{M_NS}}}oMathPara', nsmap=nsmap)
    
    oMath = etree.SubElement(oMathPara, f'{{{M_NS}}}oMath')
    _add_text(oMath, 'hist')
    _add_sub(oMath, 'k')
    _add_text(oMath, ' = ')
    
    # 累加
    nary = etree.SubElement(oMath, f'{{{M_NS}}}nary')
    naryPr = etree.SubElement(nary, f'{{{M_NS}}}naryPr')
    chr_el = etree.SubElement(naryPr, f'{{{M_NS}}}chr')
    chr_el.set(f'{{{M_NS}}}val', '∑')
    limLoc = etree.SubElement(naryPr, f'{{{M_NS}}}limLoc')
    limLoc.set(f'{{{M_NS}}}val', 'undOvr')
    
    sub = etree.SubElement(nary, f'{{{M_NS}}}sub')
    _add_text(sub, 'p∈cell')
    _add_sub(sub, 'k')
    e = etree.SubElement(nary, f'{{{M_NS}}}e')
    _add_text(e, '|∇I(p)|')
    
    _add_text(oMath, ',  |∇I| = ')
    
    # 根号
    rad = etree.SubElement(oMath, f'{{{M_NS}}}rad')
    radPr = etree.SubElement(rad, f'{{{M_NS}}}radPr')
    degHide = etree.SubElement(radPr, f'{{{M_NS}}}degHide')
    degHide.set(f'{{{M_NS}}}val', '1')
    deg = etree.SubElement(rad, f'{{{M_NS}}}deg')
    e_rad = etree.SubElement(rad, f'{{{M_NS}}}e')
    _add_text(e_rad, 'G')
    _add_sup(e_rad, '2')
    _add_text(e_rad, ' + G')
    _add_sub(e_rad, 'y')
    _add_sup(e_rad, '2')
    
    _add_text(oMath, ',  θ = arctan(G')
    _add_sub(oMath, 'y')
    _add_text(oMath, '/G')
    _add_sub(oMath, 'x')
    _add_text(oMath, ')')
    
    return [oMathPara]


def _build_formula4():
    """公式4: YOLOv3损失函数（简化版）"""
    nsmap = {'m': M_NS, 'w': W_NS}
    oMathPara = etree.Element(f'{{{M_NS}}}oMathPara', nsmap=nsmap)
    
    # L1 = ...
    oMath1 = etree.SubElement(oMathPara, f'{{{M_NS}}}oMath')
    _add_text(oMath1, 'L')
    _add_sub(oMath1, '1')
    _add_text(oMath1, ' = λ')
    _add_sub(oMath1, 'obj')
    _add_text(oMath1, '∑')
    _add_sub(oMath1, 'ij')
    _add_sup(oMath1, 'obj')
    _add_text(oMath1, '[C')
    _add_sub(oMath1, 'i')
    _add_text(oMath1, ' - ')
    # Ĉi 用 ̂ 组合字符
    r_hat = etree.SubElement(oMath1, f'{{{M_NS}}}r')
    t_hat = etree.SubElement(r_hat, f'{{{W_NS}}}t')
    t_hat.text = 'Ĉ'
    _add_sub(oMath1, 'i')
    _add_text(oMath1, ']²')
    
    # + λ_noobj...
    oMath2 = etree.SubElement(oMathPara, f'{{{M_NS}}}oMath')
    _add_text(oMath2, ' + λ')
    _add_sub(oMath2, 'noobj')
    _add_text(oMath2, '∑')
    _add_sub(oMath2, 'ij')
    _add_sup(oMath2, 'noobj')
    _add_text(oMath2, '[C')
    _add_sub(oMath2, 'i')
    _add_text(oMath2, ' - ')
    r_hat2 = etree.SubElement(oMath2, f'{{{M_NS}}}r')
    t_hat2 = etree.SubElement(r_hat2, f'{{{W_NS}}}t')
    t_hat2.text = 'Ĉ'
    _add_sub(oMath2, 'i')
    _add_text(oMath2, ']²')
    
    return [oMathPara]


def _add_text(parent, text):
    """添加普通文本run"""
    r = etree.SubElement(parent, f'{{{M_NS}}}r')
    t = etree.SubElement(r, f'{{{W_NS}}}t')
    t.text = text


def _add_sub(parent, text):
    """添加下标"""
    sub = etree.SubElement(parent, f'{{{M_NS}}}sub')
    r = etree.SubElement(sub, f'{{{M_NS}}}r')
    t = etree.SubElement(r, f'{{{W_NS}}}t')
    t.text = text


def _add_sup(parent, text):
    """添加上标"""
    sup = etree.SubElement(parent, f'{{{M_NS}}}sup')
    r = etree.SubElement(sup, f'{{{M_NS}}}r')
    t = etree.SubElement(r, f'{{{W_NS}}}t')
    t.text = text


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
        
        # 注册命名空间
        nsmap = {'w': W_NS, 'm': M_NS}
        
        formula_idx = [0]  # 闭包变量
        
        # 找到所有段落
        paragraphs = root.findall('.//{' + W_NS + '}p')
        paras_to_remove = []
        
        for para in paragraphs:
            text = ''.join(t.text or '' for t in para.iter('{' + W_NS + '}t'))
            if '？代码？' in text:
                if formula_idx[0] < 4:
                    # 清空段落内容，插入OMML
                    for child in list(para):
                        para.remove(child)
                    
                    # 添加OMML公式元素
                    formula_elements = make_formula_element(formula_idx[0] + 1)
                    for el in formula_elements:
                        para.append(el)
                    
                    formula_idx[0] += 1
                    print(f"已替换公式 {formula_idx[0]}")
        
        # 保存修改后的XML
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
    print("生成OMML公式版文档（XML直接操作）")
    print("=" * 55)

    if not os.path.exists(DOC_SRC):
        print(f"源文件不存在: {DOC_SRC}")
        return

    insert_formulas(DOC_SRC, DOC_DST)


if __name__ == "__main__":
    main()
