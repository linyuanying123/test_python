import os
import logging
from pdf2docx import Converter

logger = logging.getLogger(__name__)

class PdfToWordService:
    @staticmethod
    def convert_pdf_to_word(pdf_path, output_dir):
        """
        将PDF文件转换为Word文档
        :param pdf_path: PDF文件路径
        :param output_dir: 输出目录
        :return: 转换后的Word文件路径
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            file_name = os.path.basename(pdf_path).replace('.pdf', '.docx')
            output_path = os.path.join(output_dir, file_name)
            
            logger.info(f"开始转换PDF到Word: {pdf_path}")
            cv = Converter(pdf_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()
            
            logger.info(f"PDF转换Word成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF转Word失败: {str(e)}")
            raise
