#!/usr/bin/env python3
import json
import os
import re
import argparse
import logging
import datetime
import sys
from typing import List, Dict, Any, Optional, Tuple

# 配置日志
def setup_logging(verbose: bool = False):
    """设置日志配置"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

# 读取JSON文件
def read_chat_json(file_path: str) -> Optional[Dict[str, Any]]:
    """读取JSON文件并返回其内容
    
    Args:
        file_path: JSON文件的路径
        
    Returns:
        解析后的JSON数据，如果失败则返回None
    """
    logger = logging.getLogger(__name__)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"成功读取JSON文件: {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"解析JSON文件时出错: {file_path}, 错误: {e}")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"文件编码错误: {file_path}, 尝试使用utf-8编码, 错误: {e}")
        # 尝试使用其他编码
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                data = json.load(f)
            logger.warning(f"成功使用latin-1编码读取文件: {file_path}")
            return data
        except Exception as e2:
            logger.error(f"再次尝试读取文件失败: {e2}")
            return None
    except Exception as e:
        logger.error(f"读取文件时出错: {file_path}, 错误: {e}")
        return None

# 提取并处理对话内容 - 特别为Google AI Studio导出的格式优化
def extract_conversation(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """从数据中提取对话内容
    
    Args:
        data: 解析后的JSON数据
        
    Returns:
        提取的对话列表，每个对话包含role和content字段
    """
    logger = logging.getLogger(__name__)
    
    if not data:
        logger.warning("没有数据可供提取对话内容")
        return []
    
    # 查看JSON结构的键，了解数据组织方式
    logger.debug(f"JSON文件结构的顶层键: {list(data.keys())}")
    
    # 从之前的观察，这个文件有特殊的结构
    # 我们需要直接解析文件内容来处理这种情况
    return parse_file_optimized(data)

# 优化的文件解析方法，专门处理Google AI Studio导出的格式
def parse_file_optimized(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """优化的文件解析方法，专门处理Google AI Studio导出的格式
    
    Args:
        data: 解析后的JSON数据
        
    Returns:
        提取的对话列表
    """
    logger = logging.getLogger(__name__)
    
    # 从之前看到的内容，我们知道text和role字段是嵌套在特定结构中的
    # 让我们从数据中直接提取所有text和role字段
    fragments_with_roles = []
    extract_text_fragments(data, fragments_with_roles)
    
    logger.debug(f"提取到 {len(fragments_with_roles)} 个文本片段")
    
    # 合并连续的文本片段，使用原始的角色信息
    merged_conversations = merge_text_fragments(fragments_with_roles)
    
    return merged_conversations

# 递归提取所有text字段的内容和对应的role字段，但过滤掉大模型的思考部分和parts字段
def extract_text_fragments(obj: Any, fragments_with_roles: List[Dict[str, str]]) -> None:
    """递归提取所有text字段的内容和对应的role字段，但过滤掉大模型的思考部分和parts字段
    
    Args:
        obj: 要递归解析的对象
        fragments_with_roles: 收集文本片段的列表
    """
    logger = logging.getLogger(__name__)
    try:
        if isinstance(obj, dict):
            # 检查是否是大模型的思考部分，如果是则跳过
            if obj.get('isThought', False):
                return
            
            # 检查是否同时有text和role字段
            if 'text' in obj and 'role' in obj:
                # 确保text和role是字符串类型
                text = str(obj['text']).strip() if obj['text'] else ''
                role = str(obj['role']).strip().lower() if obj['role'] else ''
                
                if text:
                    # 将角色统一转换为'user'或'assistant'
                    if role == 'user':
                        fragments_with_roles.append({'text': text, 'role': 'user'})
                    elif role == 'model':
                        fragments_with_roles.append({'text': text, 'role': 'assistant'})
            # 递归处理字典的其他部分，但跳过parts字段以避免内容重复
            for key, value in obj.items():
                if key != 'parts':  # 跳过parts字段
                    extract_text_fragments(value, fragments_with_roles)
        elif isinstance(obj, list):
            # 递归处理列表中的每个元素
            for item in obj:
                extract_text_fragments(item, fragments_with_roles)
    except Exception as e:
        logger.error(f"提取文本片段时出错: {e}")

# 合并文本片段，使用原始的角色信息
def merge_text_fragments(fragments_with_roles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """合并文本片段，使用原始的角色信息
    
    Args:
        fragments_with_roles: 带有角色信息的文本片段列表
        
    Returns:
        合并后的对话列表
    """
    logger = logging.getLogger(__name__)
    conversations = []
    
    # 初始化当前对话的角色和内容
    if fragments_with_roles:
        current_role = fragments_with_roles[0]['role']
        current_content = fragments_with_roles[0]['text']
    else:
        logger.warning("没有文本片段可供合并")
        return []
    
    try:
        # 从第二个片段开始处理
        for fragment in fragments_with_roles[1:]:
            text = fragment['text']
            role = fragment['role']
            
            # 处理转义字符
            text = text.replace('\\n', '\n').replace('\\"', '"')
            
            # 如果角色相同且内容适合合并，则合并到当前内容
            if role == current_role and not ('.' in text[:10] or '\n' in text[:10]):
                current_content += " " + text
            else:
                # 否则，保存当前对话并开始新的对话
                conversations.append({"role": current_role, "content": current_content})
                current_role = role
                current_content = text
        
        # 添加最后一段内容
        if current_content:
            conversations.append({"role": current_role, "content": current_content})
            
        logger.debug(f"合并后得到 {len(conversations)} 条对话消息")
    except Exception as e:
        logger.error(f"合并文本片段时出错: {e}")
    
    return conversations

# 处理内容格式，包括换行和粗体
def process_formatting(content: str) -> str:
    """处理内容格式，包括换行和粗体等Markdown格式
    
    Args:
        content: 原始内容字符串
        
    Returns:
        处理后的格式化内容
    """
    # 确保换行符正确显示
    content = content.replace('\\n', '\n')
    
    # 保留原始的Markdown格式（粗体等）
    return content

# 将对话内容转换为易读的Markdown格式
def format_conversation(conversations: List[Dict[str, str]], title: str = "Google AI Studio 对话记录") -> str:
    """将对话内容转换为易读的Markdown格式
    
    Args:
        conversations: 对话列表
        title: 文档标题
        
    Returns:
        格式化的Markdown文本
    """
    formatted_text = f"# {title}\n\n"
    
    for i, conv in enumerate(conversations):
        role = conv["role"].capitalize()
        content = conv["content"]
        
        # 处理内容格式
        content = process_formatting(content)
        
        # 添加角色标记和内容（使用Markdown格式）
        formatted_text += f"## {role}\n\n{content}\n\n"
        
        # 在不同轮次对话之间添加分隔线
        if i < len(conversations) - 1:
            if conversations[i+1]["role"] != conv["role"]:
                formatted_text += "---\n\n"
    
    return formatted_text

# 保存处理后的对话到文件
def save_conversation(formatted_text: str, output_path: str, force: bool = False) -> bool:
    """保存处理后的对话到文件
    
    Args:
        formatted_text: 格式化后的对话文本
        output_path: 输出文件路径
        force: 是否强制覆盖已存在的文件
        
    Returns:
        保存是否成功
    """
    logger = logging.getLogger(__name__)
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(f"创建输出目录: {output_dir}")
        
        # 检查文件是否已存在
        if os.path.exists(output_path) and not force:
            logger.warning(f"输出文件已存在，请使用 --force 参数覆盖: {output_path}")
            return False
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        logger.info(f"对话已保存到: {output_path}")
        return True
    except Exception as e:
        logger.error(f"保存文件时出错: {e}")
        return False

# 备用的文件直接解析方法
def parse_file_directly(file_path: str) -> List[Dict[str, str]]:
    """备用的文件直接解析方法，当JSON解析失败时使用
    
    Args:
        file_path: 文件路径
        
    Returns:
        提取的对话列表
    """
    logger = logging.getLogger(__name__)
    conversations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取整个文件
            content = f.read()
            
            # 使用正则表达式提取所有text字段的内容
            text_pattern = r'"text":\s*"([^"]*)"'  # 匹配 "text": "内容" 格式
            matches = re.findall(text_pattern, content)
            
            # 合并相邻的文本片段，避免过于零散的对话
            merged_content = ""
            for i, match in enumerate(matches):
                if match.strip():
                    # 解码转义字符
                    fragment = match.replace('\\n', '\n').replace('\\"', '"')
                    
                    # 简单的合并规则：如果前一个片段以句号、问号或感叹号结尾，开始新的段落
                    if merged_content and (merged_content[-1] in '.?!。？！\n' or len(merged_content) > 2000):
                        # 根据位置交替角色
                        role = "user" if i % 5 == 0 else "assistant"  # 假设用户发言较少
                        conversations.append({"role": role, "content": merged_content})
                        merged_content = fragment
                    else:
                        if merged_content:
                            merged_content += " " + fragment
                        else:
                            merged_content = fragment
            
            # 添加最后一段内容
            if merged_content:
                conversations.append({"role": "assistant", "content": merged_content})
            
            logger.info(f"直接解析文件找到 {len(conversations)} 条合并后的对话")
    except Exception as e:
        logger.error(f"直接解析文件时出错: {e}")
    
    return conversations

# 处理单个文件的函数
def process_single_file(input_file: str, output_file: str, force: bool = False, title: str = None) -> bool:
    """处理单个文件的函数
    
    Args:
        input_file: 输入JSON文件路径
        output_file: 输出Markdown文件路径
        force: 是否强制覆盖已存在的文件
        title: 文档标题（默认使用文件名）
        
    Returns:
        处理是否成功
    """
    logger = logging.getLogger(__name__)
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        logger.error(f"文件不存在: {input_file}")
        return False
    
    logger.info(f"开始处理文件: {input_file}")
    start_time = datetime.datetime.now()
    
    # 如果没有指定标题，使用文件名作为标题
    if title is None:
        title = os.path.splitext(os.path.basename(input_file))[0]
    
    # 读取JSON文件
    data = read_chat_json(input_file)
    if not data:
        logger.warning(f"无法解析{input_file}的JSON文件，尝试直接解析文件内容...")
        # 如果无法解析JSON，尝试直接读取文件内容
        conversations = parse_file_directly(input_file)
        if not conversations:
            logger.error(f"{input_file}的所有解析尝试都失败了")
            return False
    else:
        # 提取对话内容
        conversations = extract_conversation(data)
        
        if not conversations:
            logger.warning(f"{input_file}中没有找到对话内容，尝试另一种解析方式...")
            conversations = parse_file_directly(input_file)
            if not conversations:
                logger.error(f"{input_file}的所有解析尝试都失败了")
                return False
    
    # 格式化对话
    formatted_text = format_conversation(conversations, title)
    
    # 保存对话
    success = save_conversation(formatted_text, output_file, force)
    
    if success:
        logger.info(f"{input_file}处理完成！共提取了 {len(conversations)} 条消息")
    
    end_time = datetime.datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()
    logger.debug(f"处理耗时: {elapsed_time:.2f} 秒")
    
    return success

# 批量处理文件
def batch_process_files(file_pairs: List[Tuple[str, str]], force: bool = False, title: str = None) -> bool:
    """批量处理多个文件
    
    Args:
        file_pairs: 输入输出文件路径对列表
        force: 是否强制覆盖已存在的文件
        title: 文档标题（默认使用文件名）
        
    Returns:
        所有文件是否都处理成功
    """
    logger = logging.getLogger(__name__)
    all_success = True
    
    # 批量处理文件
    for i, (input_file, output_file) in enumerate(file_pairs):
        logger.info(f"处理文件 {i+1}/{len(file_pairs)}: {input_file}")
        success = process_single_file(input_file, output_file, force, title)
        if not success:
            all_success = False

    return all_success

# 解析命令行参数
def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='将Google AI Studio导出的JSON对话记录转换为易读的Markdown格式',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('input_file', nargs='?', help='输入JSON文件路径')
    parser.add_argument('-o', '--output', help='输出Markdown文件路径')
    parser.add_argument('-f', '--force', action='store_true', help='强制覆盖已存在的输出文件')
    parser.add_argument('-t', '--title', help='生成的Markdown文档标题')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--batch', action='store_true', help='批量处理预定义的文件')
    
    return parser.parse_args()

# 主函数
def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志
    logger = setup_logging(args.verbose)
    
    # 创建输出目录（如果不存在）
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_md")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"创建输出目录: {output_dir}")
    
    if args.batch:
        # 批量处理目录中的所有相关文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        files_to_process = []
        
        # 遍历当前目录中的所有文件
        for filename in os.listdir(current_dir):
            file_path = os.path.join(current_dir, filename)
            
            # 只处理文件（非目录）且不处理已生成的.md文件
            if os.path.isfile(file_path) and not filename.endswith('.md') and not filename.endswith('.py'):
                # 创建对应的输出文件路径，将其放在output_md文件夹中
                output_file = os.path.join(output_dir, f"{filename}.md")
                files_to_process.append((file_path, output_file))
        
        logger.info(f"找到 {len(files_to_process)} 个文件需要处理")
        
        success = batch_process_files(files_to_process, args.force, args.title)
        
        if success:
            logger.info(f"所有文件处理完毕，已保存到 {output_dir}")
        else:
            logger.warning("部分文件处理失败！")
    elif args.input_file:
        # 处理单个文件
        # 如果没有指定输出文件，使用与输入文件相同的文件名但扩展名为.md，并放在output_md文件夹中
        if not args.output:
            base_name = os.path.basename(args.input_file)
            output_file = os.path.join(output_dir, f"{base_name}.md")
        else:
            output_file = args.output
        
        success = process_single_file(args.input_file, output_file, args.force, args.title)
        
        if success:
            logger.info("文件处理完成！")
        else:
            logger.error("文件处理失败！")
    else:
        # 显示帮助信息
        print("请提供输入文件路径，或使用--batch参数批量处理文件。")
        print("使用-h或--help查看完整用法。")
        return

if __name__ == "__main__":
    main()