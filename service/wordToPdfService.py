import os
import win32com.client
from tkinter import Tk, filedialog
from pathlib import Path
from ..utils import logUtils
import logging

logger = logging.getLogger(__name__)

def word_to_pdf(input_path=None, output_path=None):
    """
    将Word文档转换为PDF
    :param input_path: Word文件路径(可选)
    :param output_path: 输出PDF路径(可选)
    :return: 转换后的PDF路径
    """
    try:
        # 如果没有提供输入路径，则弹出文件选择对话框
        if not input_path:
            root = Tk()
            root.withdraw()
            input_path = filedialog.askopenfilename(
                title="选择Word文档",
                filetypes=[("Word文档", "*.docx *.doc")]
            )
            if not input_path:
                return None

        # 如果没有指定输出路径，则在同目录下生成同名PDF
        if not output_path:
            output_path = os.path.splitext(input_path)[0] + '.pdf'

        # 调用Word应用程序进行转换
        word = win32com.client.Dispatch("Word.Application")
        doc = word.Documents.Open(input_path)
        doc.SaveAs(output_path, FileFormat=17)  # 17是PDF格式代码
        doc.Close()
        word.Quit()

        logger.info(f"成功将 {input_path} 转换为 {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Word转PDF失败: {e}", exc_info=True)
        return None

def word_to_pdf_entrypoint():
    """提供给主菜单调用的入口函数"""
    print("\n=== Word转PDF工具 ===")
    result = word_to_pdf()
    if result:
        print(f"转换成功! PDF已保存到: {result}")
    else:
        print("转换失败或已取消")
    input("按任意键返回主菜单...")
