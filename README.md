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
</p>
<p align="center">

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
        <ul>
            <li><a href="#创建您的第一个模型">创建您的第一个模型</a></li>
            <li><a href="#将数据保存到数据库">将数据保存到数据库</a></li>
            <li><a href="#查找符合条件的文档">查找符合条件的文档</a></li>
            <li><a href="#修改数据库中的文档">修改数据库中的文档</a></li>
            <li><a href="#嵌入式模型">嵌入式模型</a></li>
            <li><a href="#连接数据库">连接数据库</a></li>
        </ul>
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

### 创建您的第一个模型

Mango 包含强大的声明性模型，它使用起来就像 Pydantic 模型一样，看看下面这个例子：

```python
from mango import Field, Model


class Fruit(Model):
    name: str
    price: int = Field(gt=0)  # 价格应不小于0元
```

通过定义 `Fruit` 类，我们创建了一个 Mango 模型。

每个 Mango 模型也是一个 Pydantic 模型，所以您也可以使用各种 Pydantic 验证器进行复杂的验证！

`Fruit` 模型在数据库中的集合名称是 `fruit`，我们也可以给它起一个不同的名字。

```python
class Fruit(Model, name="goods"):
    name: str
    price: int = Field(gt=0)
```

### 将数据保存到数据库

接下来让我们使用它来将水果的数据保存到数据库。

```python
# 创建一个实例并保存它
fruit = await Fruit(name="mango", price=100).save()
```
### 查找符合条件的文档

现在我们可以从数据库中获取一些数据。

```python
# 通过主键查询文档，会返回单独的实例
fruit = await Fruit.get(fruit.id)
```

Mango 提供了丰富的查询语言，允许您使用 Python 表达式来查询 MongoDB。

```python
# 通过条件查询文档，会返回实例列表
fruits = await Fruit.find(Fruit.name == "mango")

# 异步迭代获得实例
async for fruit in Fruit.find(Fruit.name == "mango"):
    print(fruit)
```
您也可以使用与 PyMongo/Motor 相同的模式进行查询：

```python
fruits = await Fruit.find({"name": "mango"})
fruits = await Fruit.find({Fruit.name: "mango"})
```
### 修改数据库中的文档

```python
# 使用结果集上的 get 方法，可以获得单个实例
fruit = await Fruit.find(Fruit.name == "mango").get()

# 修改水果的价格并保存
fruit.price = 200
await fruit.update()

# 我们也可以使用另一种方式
await fruit.update(price=300)
```
### 嵌入式模型

Mango 也可以存储和查询内嵌文档。

```python
from mango import Field, Model

# 定义内嵌文档模型
class Address(Model, embedded=True):
    city: str
    country: str


class Fruit(Model):
    name: str
    price: int = Field(gt=0)
    address: Address  # 内嵌模型


address = Address(city="any", country="unknown")
fruit = await Fruit(name="mango", price=100, address=address).save()

# 通过内嵌文档查询
await Fruit.find(fruit.address.city == "any")
```

### 连接数据库

实际上，如果没有显式连接数据库，那么 Mango 将默认连接到 `mongodb://localhost:27017` 的 `test` 数据库，就像我们一开始做的那样。

我们也可以显式指定连接的 MongoDB：

```python
from mango import connect

# 连接到 mongodb://localhost:27017 的 mango 数据库
connect("mango")

# 连接到 mongodb://localhost:12345 的 test 数据库
connect(uri="mongodb://localhost:12345")

# 连接到 mongodb://localhost:12345 的 mango 数据库
connect("mango", uri="mongodb://localhost:12345")
```

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