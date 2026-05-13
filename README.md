# 公文排版助手 V1.3

| 项目 | 内容 |
| --- | --- |
| 文档编号 | GWP-README-001 |
| 文档版本 | V1.3 |
| 更新日期 | 2026-05-13 |
| 适用范围 | 项目简介、运行方式、版本概览、文档导航 |

## 项目简介

公文排版助手是一款 Windows 桌面便携软件，用于将导入或粘贴的文字内容按照公文排版参数重新整理，并导出为 `.docx` 文档。

软件面向日常公文、通知、汇报材料、总结材料等场景，重点解决“文字内容已有，但格式需要统一”的重复排版工作。

## 当前版本

- 产品名称：公文排版助手
- 当前版本：V1.3
- 发布形式：Windows 便携版
- 主程序名称：`公文排版助手V1_3.exe`
- 本地打包输出：`dist_release/公文排版助手V1_3/公文排版助手V1_3.exe`
- GitHub Release 附件：`公文排版助手V1_3-windows-portable.zip`

## 核心功能

- 导入 `.docx` 和 `.txt` 文件
- 在编辑区直接粘贴、输入和修改文字
- 导入文档后自动清除原格式，仅保留文字和段落结构
- 自动识别文档标题、一级标题、二级标题和正文
- 设置页边距、固定行距、字体和字号
- 加载 Windows 本地字体，并加入字体下拉菜单
- 删除软件中显示的字体选项
- 保存当前参数为默认模板
- 保存默认导出文件夹
- 导出排版后的 `.docx` 文档

## V1.3 更新摘要

- 主界面升级为更舒展的 `1030 x 613` 布局
- 字体、按钮、输入框、下拉框和区域间距重新校准
- 生成按钮改为深灰绿色 `#5F7450`
- 修复外接显示器、复制投影和不同 DPI 缩放下的文字定位问题
- 修复“正文”标题和底部联系方式在特殊显示模式下跑偏的问题
- 默认字体调整为：文档标题、二级标题、正文为仿宋，一级标题为黑体
- 段落固定行距单位显示为“磅”
- GitHub Actions 支持自动编译 Windows 便携版并发布 Release

## 普通用户运行方式

1. 打开 GitHub Release 页面。
2. 下载 `公文排版助手V1_3-windows-portable.zip`。
3. 解压压缩包。
4. 双击 `公文排版助手V1_3.exe`。

普通用户不需要安装 Python、PySide6、python-docx 或 PyInstaller。

## 开发环境运行

在项目根目录执行：

```powershell
python -m pip install -r requirements.txt
python app/main.py
```

## 本地打包

在项目根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_portable.ps1
```

打包成功后，输出目录为：

```text
dist_release/公文排版助手V1_3
```

## 项目文档

- [用户使用说明](用户使用说明.md)
- [开发文档](开发文档.md)
- [界面设计规范](界面设计规范.md)
- [版本更新记录](版本更新记录.md)
- [Release Notes](RELEASE_NOTES.md)

## 技术栈

- Python
- PySide6
- python-docx
- PyInstaller
- GitHub Actions
