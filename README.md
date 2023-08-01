<p align="center">
    <a name="readme-top"></a>
    <a href="https://github.com/A-kirami/mango">
        <img width="140px" src="https://raw.githubusercontent.com/A-kirami/mango/main/assets/mango-logo.svg" align="center" alt="Mango" />
    </a>
    <h1 align="center">Mango</h1>
    <p align="center">🥭 带有类型提示的 Python 异步 MongoDB 对象文档映射器</p>
</p>
<p align="center">
    <a href="./LICENSE">
        <img src="https://img.shields.io/github/license/A-kirami/mango.svg" alt="license">
    </a>
    <a href="https://pypi.python.org/pypi/mango-odm">
        <img src="https://img.shields.io/pypi/v/mango-odm.svg" alt="pypi">
    </a>
    <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">
    </a>
</p>
<p align="center">
    <a href="#-示例">查看演示</a>
    ·
    <a href="https://github.com/A-kirami/mango/issues/new?assignees=&labels=bug&template=bug_report.yml&title=%5BBUG%5D%3A+">错误报告</a>
    ·
    <a href="https://github.com/A-kirami/mango/issues/new?assignees=&labels=enhancement&template=feature_request.yml&title=%5BFeature%5D%3A+">功能请求</a>
</p>
<p align="center">
    <strong>简体中文</strong>
    ·
    <a href="/docs/README_EN.md">English</a>
    ·
    <a href="/docs/README_JA.md">日本語</a>
</p>

## 🔖 目录

<details open="open">
  <summary>目录</summary>
  <ul>
    <li>
        <a href="#-简介">简介</a>
        <ul>
            <li><a href="#-核心特性">核心特性</a></li>
        </ul>
    </li>
    <li>
        <a href="#-安装">安装</a>
        <ul>
            <li><a href="#PIP">PIP</a></li>
            <li><a href="#Poetry">Poetry</a></li>
        </ul>
    </li>
    <li>
        <a href="#-示例">示例</a>
    </li>
    <li>
        <a href="#-贡献">贡献</a>
        <ul>
            <li><a href="#-鸣谢">鸣谢</a></li>
        </ul>
    </li>
    <li><a href="#-支持">支持</a></li>
    <li><a href="#-许可证">许可证</a></li>
  </ul>
</details>

## 📖 简介

Mango 是一个带有类型提示的 Python 异步 MongoDB 对象文档映射器(ODM)，它构建在 [Motor](https://motor.readthedocs.io/en/stable/) 和 [Pydantic](https://pydantic-docs.helpmanual.io/) 之上。

Mango 使得数据建模和查询变得非常容易，帮助您关注应用程序中真正重要的部分。

### ✨ 核心特性：

- **完善的类型标注**：利用静态分析来减少运行时问题
- **简洁流畅的 API**：更易于学习和使用，提高开发效率
- **优雅的编辑器支持**：自动完成无处不在，从对象创建到查询结果

<p align="right">[<a href="#readme-top">⬆回到顶部</a>]</p>

## 🚀 安装

### PIP

```shell
pip install mango-odm
```
### Poetry

```shell
poetry add mango-odm
```

<p align="right">[<a href="#readme-top">⬆回到顶部</a>]</p>

## 🌟 示例

```python
import asyncio

from mango import Document, EmbeddedDocument, Field, Mango


# 嵌入式文档
class Author(EmbeddedDocument):
    name: str
    profile: str | None = None


# Mango 文档模型
class Book(Document):
    name: str = Field(primary_key=True)  # 将字段设置为主键，如果不显式指定主键，则会自动创建 id 字段作为主键
    summary: str | None = None
    author: Author  # 嵌入文档
    price: int = Field(index=True)  # 为字段添加索引


async def main():
    # 初始化 Mango，它会创建连接并初始化文档模型，你可以传入 db 或者 uri 参数来指定连接
    await Mango.init()

    # 像 pydantic 的模型一样使用
    book = Book(name="book", author=Author(name="author"), price=10)
    # 将它插入到数据库中
    await book.save()

    # Mango 提供了丰富的查询语言，允许您使用 Python 表达式来查询
    if book := await Book.find(Book.price <= 20, Book.author.name == "author").get():
        # 更新文档的 summary 字段
        book.summary = "summary"
        await book.update()


if __name__ == "__main__":
    asyncio.run(main())

```

<p align="right">[<a href="#readme-top">⬆回到顶部</a>]</p>

## 🤝 贡献

想为这个项目做出一份贡献吗？[点击这里]()阅读并了解如何贡献。

### 🎉 鸣谢

感谢以下开发者对该项目做出的贡献：

<a href="https://github.com/A-kirami/mango/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=A-kirami/mango" />
</a>

<p align="right">[<a href="#readme-top">⬆回到顶部</a>]</p>

## 💖 支持

喜欢这个项目？请点亮 star 并分享它！

<p align="right">[<a href="#readme-top">⬆回到顶部</a>]</p>

## 📝 许可证

在 `MIT` 许可证下分发。请参阅 [LICENSE](./LICENSE) 以获取更多信息。

<p align="right">[<a href="#readme-top">⬆回到顶部</a>]</p>