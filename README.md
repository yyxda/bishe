# Argus - 钓鱼邮件检测系统

## 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- uv (Python 包管理器)

## 部署步骤

### 1. 克隆项目

```bash
git clone https://github.com/HierarchThurs/Argus.git
cd Argus
```

### 2. 初始化数据库

创建数据库Argus，运行SQL文件建表

```bash
./docs/Argus.sql
```

> 默认管理员账号：`Administrator` / 密码：`Administrator`

### 3. 配置后端

```bash
cd backend
cp .env-example .env
```

编辑 `.env` 文件，修改数据库连接信息：

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=Argus
```

### 4. 安装后端依赖并启动

```bash
cd backend
uv sync
uv run --env-file .env python -m app.main
```

后端默认运行在 `http://localhost:10003`

### 5. 安装前端依赖并启动

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`

# 前置环境安装

## 安装npm

### 第一步：更新系统并安装 curl

首先确保你的系统软件包是最新的，并且安装了 `curl`（用于下载安装脚本）。

```bash
sudo apt update
sudo apt install curl -y
```

### 第二步：下载并安装 nvm

运行以下命令从官方 GitHub 仓库下载并运行 nvm 安装脚本（当前稳定版本为 v0.39.7）：

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

> **注意：** 如果你无法连接 GitHub，可能需要检查网络设置或使用代理。

### 第三步：激活 nvm

安装脚本会自动将配置写入你的 `~/.bashrc` 文件，但你需要刷新当前的终端会话才能使 nvm 生效：

Bash

```
source ~/.bashrc
```

验证 nvm 是否安装成功：

```bash
nvm --version
```

*如果输出了版本号（如 0.40.3），说明 nvm 已就绪。*

------

### 第四步：安装 Node.js 和 npm

nvm 安装好后，就可以用来安装 Node.js 了。Node.js 安装包中会自动包含 **npm**。

**推荐安装 LTS（长期支持）版本**，这是最稳定且适合大多数项目的版本：

```bash
nvm install --lts
```

### 第五步：验证安装

检查 Node.js 和 npm 是否安装成功：

```bash
node -v
npm -v
```

------

### 常用 nvm 命令速查表

| **命令**                      | **作用**                                   |
| ----------------------------- | ------------------------------------------ |
| `nvm install <version>`       | 安装指定版本 (例如: `nvm install 18`)      |
| `nvm use <version>`           | 切换到指定版本                             |
| `nvm ls`                      | 列出已安装的所有版本                       |
| `nvm ls-remote`               | 列出网上所有可供安装的版本                 |
| `nvm alias default <version>` | 设置默认版本（打开新终端时自动使用的版本） |

## 安装uv

### 第一步：使用官方安装脚本

**使用 curl 安装：**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 第二步：使命令生效

安装完成后，安装程序通常会自动修改你的 shell 配置文件（如`~/.bashrc` 或 `~/.zshrc`）。

为了让 uv 命令立即生效，你可以关闭并重新打开终端，或者运行以下命令刷新配置：

```bash
source ~/.bashrc
```

### 第三步：验证安装

检查 uv 是否安装成功及其版本：

```bash
uv --version
```

*如果看到类似 `uv 0.x.x` 的输出，说明安装成功。*

------

### 🚀 uv 常用命令速查

uv 的用法非常符合直觉，很多命令和 pip 类似：

| **任务**           | **传统命令**                      | **uv 命令**                          |
| ------------------ | --------------------------------- | ------------------------------------ |
| **创建虚拟环境**   | `python -m venv .venv`            | `uv venv` (速度极快)                 |
| **安装包**         | `pip install requests`            | `uv pip install requests`            |
| **从文件安装依赖** | `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| **同步依赖**       | `pip-sync`                        | `uv pip sync`                        |
| **运行脚本**       | (需激活环境) `python app.py`      | `uv run app.py` (自动管理环境)       |
