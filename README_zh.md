# Google AI Studio 对话记录转换工具

## 功能介绍
convert_chat.py 是一个将Google AI Studio导出的对话记录转换为易读Markdown格式的Python脚本。它能够批量处理多个对话文件，自动提取对话内容并格式化输出，方便保存和分享AI对话历史。

## 安装要求
- Python 3.6 或更高版本
- 无需额外安装依赖包（使用Python标准库）

## 使用方法
### 基本语法
```
python convert_chat.py [选项] [输入文件]
```

### 命令行参数
| 参数 | 说明 |
|------|------|
| -h, --help | 显示帮助信息并退出 |
| -o, --output | 指定输出Markdown文件路径 |
| -f, --force | 强制覆盖已存在的输出文件 |
| -t, --title | 生成的Markdown文档标题 |
| -v, --verbose | 显示详细日志信息 |
| --batch | 批量处理当前目录中的所有相关文件 |
| input_file | 输入JSON文件路径（单个文件处理模式） |

### 使用示例

#### 1. 单个文件处理
将单个对话文件转换为Markdown格式：
```
python convert_chat.py input.json
```

指定输出路径和标题：
```
python convert_chat.py input.json -o output.md -t "我的AI对话"
```

强制覆盖已存在的输出文件：
```
python convert_chat.py input.json -f
```

#### 2. 批量文件处理
自动处理当前目录中所有非Markdown和非Python文件：
```
python convert_chat.py --batch
```

批量处理并强制覆盖现有文件：
```
python convert_chat.py --batch --force
```

## 输出说明
- 所有生成的Markdown文件默认保存在`output_md`文件夹中
- 文件名格式为`[原始文件名].md`
- 输出内容包含对话角色（User/Assistant）和完整对话内容
- 不同轮次的对话之间用分隔线`---`分隔

## 注意事项
1. 确保输入文件是Google AI Studio导出的JSON格式文件
2. 批量处理模式会自动跳过`.md`和`.py`文件
3. 如果输出目录不存在，脚本会自动创建`output_md`文件夹
4. 使用`--force`参数时要小心，它会直接覆盖已存在的文件
5. 对于大型对话文件，建议使用`--verbose`参数查看处理进度

## 故障排除
- **JSON解析错误**：确保输入文件是有效的JSON格式
- **权限问题**：检查脚本是否有读取输入文件和写入输出文件的权限
- **编码问题**：脚本默认使用UTF-8编码，对于特殊编码文件可能需要手动调整

如果遇到其他问题，请尝试使用`--verbose`参数获取详细日志信息以便排查。