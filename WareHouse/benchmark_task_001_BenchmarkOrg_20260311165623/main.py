'''
Main entry point for the Capital Information Document Generator.
This application answers the question about China's capital and generates a document with additional information.
'''
import sys
import io
from capital_facts import CapitalFacts
import datetime
# Set standard output encoding to UTF-8 to prevent encoding errors on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def generate_document():
    """Generate a text document with capital information."""
    facts = CapitalFacts()
    # Get the answer to the main question
    answer = facts.get_answer_to_question()
    # Get detailed China info
    china_info = facts.get_china_capital_info()
    # Get other capitals
    other_capitals = facts.get_all_capitals()
    # Create document content
    document_lines = []
    document_lines.append("=" * 50)
    document_lines.append("首都信息文档 | Capital Information Document")
    document_lines.append("=" * 50)
    document_lines.append(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    document_lines.append("\n")
    document_lines.append("问题: 中国的首都是哪里？")
    document_lines.append(f"答案: {answer}")
    document_lines.append("\n")
    document_lines.append("-" * 50)
    document_lines.append("中国首都详细信息:")
    document_lines.append("-" * 50)
    document_lines.append(f"国家: {china_info['country']}")
    document_lines.append(f"首都: {china_info['chinese_name']} ({china_info['capital']})")
    document_lines.append(f"人口: {china_info['population']}")
    document_lines.append(f"面积: {china_info['area']}")
    document_lines.append(f"建都时间: {china_info['established']}")
    document_lines.append("\n有趣事实:")
    for fact in china_info['facts']:
        document_lines.append(f"  • {fact}")
    document_lines.append("\n")
    document_lines.append("-" * 50)
    document_lines.append("其他主要国家首都:")
    document_lines.append("-" * 50)
    document_lines.append(f"{'国家':<15} {'首都':<20} {'人口':<15} {'面积':<10}")
    document_lines.append("-" * 50)
    for capital in other_capitals:
        if capital['country'] != 'China':
            document_lines.append(f"{capital['country']:<15} {capital['capital']:<20} {capital['population']:<15} {capital['area']:<10}")
    document_lines.append("\n")
    document_lines.append("=" * 50)
    document_lines.append("文档结束")
    # Write to file
    filename = f"capital_info_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(document_lines))
    print(f"文档已生成: {filename}")
    # Safe print with UTF-8 encoding
    print('\n'.join(document_lines))
def main():
    """Main function to generate the document."""
    generate_document()
if __name__ == "__main__":
    main()