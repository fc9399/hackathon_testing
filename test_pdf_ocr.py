#!/usr/bin/env python3
"""
测试PDF OCR功能
"""

import requests
import json
from services.s3_service import s3_service
import io
import PyPDF2
from pdf2image import convert_from_bytes
import pytesseract

def test_pdf_ocr():
    """测试PDF OCR功能"""
    try:
        # 从S3下载PDF文件
        print("📥 从S3下载PDF文件...")
        response = s3_service.client.get_object(
            Bucket='unimem-uploads-20251027',
            Key='uploads/20251027_222947_confirmation.pdf'
        )
        content = response['Body'].read()
        print(f"✅ 文件下载成功，大小: {len(content)} bytes")
        
        # 测试PyPDF2直接提取
        print("\n📄 测试PyPDF2直接提取...")
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            print(f"第{page_num+1}页文本长度: {len(page_text)}")
            text += page_text + "\n"
        
        text = text.strip()
        print(f"PyPDF2提取结果: 长度={len(text)}, 内容='{text[:100]}...'")
        
        # 如果文本为空，尝试OCR
        if not text or len(text) < 50:
            print("\n🔍 文本为空，尝试OCR...")
            try:
                # 将PDF转换为图片
                images = convert_from_bytes(content)
                print(f"PDF转换为图片成功，共{len(images)}页")
                
                ocr_text = ""
                for i, image in enumerate(images):
                    print(f"🔍 OCR处理第{i+1}页...")
                    try:
                        # 使用pytesseract进行OCR
                        page_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                        print(f"第{i+1}页OCR结果长度: {len(page_text)}")
                        ocr_text += page_text + "\n"
                    except Exception as ocr_page_error:
                        print(f"第{i+1}页OCR失败: {ocr_page_error}")
                
                if ocr_text.strip():
                    print(f"✅ OCR成功，提取文本长度: {len(ocr_text)}")
                    print(f"OCR文本预览: {ocr_text[:200]}...")
                else:
                    print("⚠️ OCR也未提取到文本")
                    
            except Exception as ocr_error:
                print(f"❌ OCR失败: {ocr_error}")
        else:
            print("✅ PyPDF2成功提取文本，无需OCR")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_pdf_ocr()
