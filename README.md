# 课程表生成器

## 项目描述
这是一个使用 PyQt5 构建的桌面应用程序，用于生成和显示课程表。它提供了一个图形用户界面来管理设置、生成课程表和查看它们。

## 主要特性
*   用户友好的图形用户界面 (GUI)
*   独立的主页、设置和生成页面
*   可自定义上午和下午的课程数量
*   以清晰的表格格式显示生成的课程表

## 文件结构
*   `main.py`: 应用程序的主要入口点。初始化主窗口和UI组件。
*   `menu.py`: 包含用于生成时间描述和在表格中显示数据帧的辅助函数。它还可能包含与 Streamlit 相关的代码，这可能用于网页版或某些实用功能。
*   `run.py`: 很可能是用于运行应用程序的脚本。
*   `pages/`: 包含应用程序不同部分/页面的 Python 文件的目录 (例如 `home.py`, `settings.py`, `generate.py`)。
*   `settings.json`, `settings.toml`: 用于存储应用程序设置的配置文件。
*   `style.py`: 可能用于设置GUI元素的样式。
*   `wr_settings.py`: 用于读取/写入设置的辅助脚本。

## 如何使用
运行此应用程序：
1.  确保已安装 Python。
2.  安装所需的库：
    ```bash
    pip install PyQt5 qfluentwidgets pandas toml
    ```
3.  执行主脚本：
    ```bash
    python main.py
    ```
    (或者，如果 `run.py` 是预期的启动脚本，则执行 `python run.py`)。
