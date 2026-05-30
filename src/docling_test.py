from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import DocItemLabel
from docling.datamodel.base_models import InputFormat
from src.schemas.pdf_parser.models import PaperFigure, PaperSection, PaperTable, ParserType, PdfContent
from docling.chunking import HierarchicalChunker

pipeline_options = PdfPipelineOptions(
            do_table_structure=True,
            do_ocr=False,  # Usually disabled for speed
        )

converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)})
result = converter.convert("src/data/arxiv_pdfs/2605.28805v1.pdf", max_num_pages=30, max_file_size=20 * 1024 * 1024)
doc =result.document

def test_doc_iterate_items():
    # 1. 初始化最终结果和临时章节容器
    sections = []
    current_section = {"title": "Content", "content": ""} 
    # 2. 适配 2.96.0：使用官方推荐的迭代器遍历元素及其层级
    for item, level in doc.iterate_items():
        # 适配 2.96.0：通过新版枚举类型判断这一块是不是大标题或小标题
        if hasattr(item, "label") and item.label in [DocItemLabel.TITLE, DocItemLabel.SECTION_HEADER]:
            
            # 如果上一个章节已经攒了正文，先打包归档
            if current_section["content"].strip():
                sections.append(PaperSection(
                    title=current_section["title"], 
                    content=current_section["content"].strip()
                ))
                
            # 清空临时容器，将当前发现的这行字设为新章节的标题
            current_section = {"title": item.text.strip(), "content": ""}
        else:
            # 普通正文元素（段落、列表、表格文字等），源源不断追加到当前章节
            if hasattr(item, "text") and item.text.strip():
                current_section["content"] += item.text + "\n"

    # 3. 循环结束后，别忘了把最后一个章节打包收尾
    if current_section["content"].strip():
        sections.append(PaperSection(
            title=current_section["title"], 
            content=current_section["content"].strip()
        ))

def test_original_content():
    # 1. 初始化最终结果和临时章节容器
    sections = []
    current_section = {"title": "Content", "content": ""}
    """Test the original content extraction."""
    for element in doc.texts:
        if hasattr(element, "label") and element.label in ["title", "section_header"]:
            # Save previous section if it has content
            if current_section["content"].strip():
                sections.append(PaperSection(title=current_section["title"], content=current_section["content"].strip()))
            # Start new section
            current_section = {"title": element.text.strip(), "content": ""}
            print(current_section)
        else:
            # Add content to current section
            if hasattr(element, "text") and element.text:
                current_section["content"] += element.text + "\n"
                print(' '.join(element.text.split()[:10]) + "..." + ' '.join(element.text.split()[-10:]))

    # Add final section
    if current_section["content"].strip():
        sections.append(PaperSection(title=current_section["title"], content=current_section["content"].strip()))

def test_chunking():
    """Test the chunking process."""
    chunker = HierarchicalChunker()
    doc_chunks = chunker.chunk(doc)
    sections = []
    current_section = {"title": "Content", "content": ""}

    # 3. 完美合体：遍历连贯的语义块
    for chunk in doc_chunks:
        # 拿到当前块所属的标题路径（例如：['1. Introduction', '1.1 Background']）
        headings = chunk.meta.headings
        
        # 💥 核心选择：如果你想按最细的子标题合并，用 headings[-1]；
        # 如果你想按 Introduction 这种大章合并，用 headings[0] 
        chunk_title = headings[0] if headings else "Content"
        
        if chunk_title != current_section["title"]:
            # 发现新标题了，先把之前积攒的旧章节归档打包
            if current_section["content"].strip():
                sections.append(PaperSection(
                    title=current_section["title"], 
                    content=current_section["content"].strip()
                ))
                print(current_section["title"])
                show_content = (" ".join(current_section["content"].split()[:10])+"..."+ " ".join(current_section["content"].split()[-10:]))
                print(show_content)
            # 开启新章节，并重置内容
            current_section = {"title": chunk_title, "content": chunk.text.strip()}
        else:
            # 💥 此时的 chunk.text 绝对是跨页无损拼接好的纯净文本，放心追加
            current_section["content"] += "\n\n" + chunk.text.strip()
    # 4. 收尾：把最后一个章节打包
    if current_section["content"].strip():
        sections.append(PaperSection(
            title=current_section["title"], 
            content=current_section["content"].strip()
        ))

if __name__ == "__main__":
    test_doc_iterate_items()
