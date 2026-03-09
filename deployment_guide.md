# Face Anti-Spoofing API 部署指南

因为本项目已经重构为标准的 **FastAPI** 应用，所以它的部署方式与其他现代 Python Web 服务（如 Django, Flask）非常类似：推荐使用 `uvicorn` (ASGI 服务器) 配合 `gunicorn` (进程管理器) 来进行生产环境的高并发部署。

## 前提要求：模型权重下载

在开始启动服务前，你需要确保本地拥有所有的模型权重文件。

**1. 手动下载活体检测权重：**
我们的 API 需要 `MiniFASNetV2.pth`。你需要在项目根目录下创建一个 `weights` 文件夹，并将权重文件放进去：

```bash
cd /path/to/face-anti-spoofing
mkdir -p weights
wget -qO weights/MiniFASNetV2.pth https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV2.pth
wget -qO weights/MiniFASNetV1SE.pth https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV1SE.pth
```

**2. 提前缓存人脸检测模型 (重要！)：**
由于底层使用了 `uniface` 的 `RetinaFace` 进行人脸裁切，它在第一次初始化（`RetinaFace()`）时，会自动尝试从网络下载检测模型（例如 `retinaface_mnet_v2.onnx`）并缓存到系统的 `~/.uniface/models/` 目录中。

如果你的**生产服务器没有外网访问权限**，或者连接 GitHub 速度极慢，启动 API 时会超时抛错。**强烈建议**在有网环境（比如本地开发机）上先运行一次代码，将生成的 `~/.uniface/models/` 文件夹完整打包，然后再拷贝到生产服务器的对应目录下（通常为 `/root/.uniface/models` 或是特定执行用户的 `home` 目录下）。

## 安装与准备

本项目使用 [`uv`](https://docs.astral.sh/uv/) 作为包管理器。请确保你已经在系统上安装了 `uv`。

```bash
# 进入项目目录
cd /path/to/face-anti-spoofing

# 【强烈建议：如果是纯 CPU 服务器】
# 通过指定 cpu extra，uv 会自动从 pytorch-cpu 镜像源拉取，而忽略 2GB+ 的完整 CUDA 版本：
uv sync --extra cpu

# 【如果是带 GPU 的服务器，需要完整的 CUDA 支持】
uv sync --extra gpu
```

---

## 方案 1：快速后台部署 (适合轻量级使用 / 测试服务器)

最简单的方法是直接使用 `nohup` 或 `screen`/`tmux` 将服务挂在后台运行，但在服务器重启后它不会自动启动。

```bash
# 激活环境
source .venv/bin/activate

# 使用后台进程启动服务 (监听所有网络接口的 8000 端口)
nohup uvicorn api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

> 提示：如果只需本机内部通信，把 `--host 0.0.0.0` 改成 `--host 127.0.0.1` 即可。

## 方案 2：Systemd 守护进程部署 (推荐在 Linux 上单机稳定运行)

为了确保服务器重启后 API 能够自动启动，且进程挂掉后能自动恢复，建议配置 Linux 的 `systemd` 服务。

**1. 创建服务配置文件：**

```bash
sudo nano /etc/systemd/system/fas-api.service
```

**2. 填入如下内容** (需把里面 `/path/to/` 替换为你实际项目的绝对路径)：

```ini
[Unit]
Description=Face Anti-Spoofing FastAPI Service
After=network.target

[Service]
User=root
# 将下面替换为你的实际项目路径
WorkingDirectory=/path/to/face-anti-spoofing
# 将下面替换为你项目中 .venv 的 uvicorn 的绝对路径
ExecStart=/path/to/face-anti-spoofing/.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**3. 开机自启：**

```bash
sudo systemctl daemon-reload
sudo systemctl start fas-api
sudo systemctl enable fas-api
```

- 测试是否成功：`sudo systemctl status fas-api`
- 查看日志：`sudo journalctl -u fas-api -f`

## 方案 3：Gunicorn + Uvicorn 生产高并发部署

如果你需要在生产环境大规模对外提供服务，单进程的 Uvicorn 会在并发请求排队时出现瓶颈。Gunicorn 配合 Uvicorn Worker 并发是 Python 社区的标准答案。

**1. 进入 uv 环境并安装 Gunicorn：**

```bash
uv add gunicorn
```

**2. 使用 Gunicorn 启动多进程：**

```bash
# 启动 4 个 Worker 进程在后台跑
uv run gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --daemon
```

这里的 `-w 4` 表示分配了 4 个进程，也就是可以同时处理至少 4 倍的并发度。你可以根据服务器的 CPU 核心数进行调整（经验上通常是 `核心数 * 2 + 1`）。同样，你也将其写入方案 2 的 `systemd` 配置以获得守护。

## 注意事项与预热

因为 `api.py` 内部这段初始化代码是在导入时同步完成加载的：
```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model, config = load_model("weights/MiniFASNetV2.pth", "v2", device)
detector = RetinaFace()
```

这意味着：
1. **启动可能稍慢**：Uvicorn / Gunicorn 在启动 worker 时，需要花一两秒钟加载 PyTorch 模型权重。这是正常的。
2. **下载检测模型（首次）**：代码初次运行如果服务器上没有 `~/.uniface/` 缓存，`RetinaFace()` 这一句会自动触发从外网下载约十多兆的模型。内网服务器的话，如果连接 github 慢可能导致第一下启动卡住乃至超时报错。建议在无网环境下启动之前，先在有网环境将 `~/.uniface/models` 打包好复制过去。
3. **显存占用**：如果你使用的是 GPU 服务器（CUDA），Gunicorn 开启多线程虽然能提高并发，但是每一个 worker (`-w X`) 都会把模型在 GPU 显存里独立拷贝一份！如果 GPU 显存比较紧张，千万别把 worker 数量设得太大。
