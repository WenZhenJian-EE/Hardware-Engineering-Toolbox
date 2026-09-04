import os
import sys
import subprocess
import time
import webbrowser

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(project_root, "backend")
    frontend_dir = os.path.join(project_root, "frontend")

    print("=========================================================")
    print("      Hardware Engineering Toolbox - 一键联合启动服务      ")
    print("=========================================================")

    # 1. 确保安装后端 Python 依赖
    print("\n[1/3] 正在检查并安装后端 Python 依赖...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", os.path.join(backend_dir, "requirements.txt")],
            check=True
        )
        print("  => 后端 Python 依赖检查与安装完成。")
    except Exception as e:
        print(f"  => 安装 Python 依赖失败 (跳过): {e}")

    # 2. 启动 FastAPI 后端服务
    print("\n[2/3] 正在启动 FastAPI 后端服务 (端口: 8000)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir,
        text=True
    )

    # 3. 启动 Vite 前端服务
    print("[3/3] 正在启动 Vite React 前端服务 (端口: 5173)...")
    # Windows 下通过 cmd /c npm run dev 执行
    npm_cmd = ["cmd", "/c", "npm run dev"] if os.name == 'nt' else ["npm", "run", "dev"]
    frontend_process = subprocess.Popen(
        npm_cmd,
        cwd=frontend_dir,
        text=True
    )

    # 4. 等待就绪并打开浏览器
    print("\n正在等待服务初始化就绪...")
    time.sleep(3.5) # 稍微多等待一下
    
    frontend_url = "http://localhost:5173"
    print(f"\n=> 启动成功！正在自动在浏览器中打开: {frontend_url}")
    webbrowser.open(frontend_url)

    print("\n---------------------------------------------------------")
    print("  提示: 按下 Ctrl+C 可以安全终止并关闭所有前后端服务进程。  ")
    print("---------------------------------------------------------")

    try:
        while True:
            # 检查子进程是否意外退出
            if backend_process.poll() is not None:
                print("\n[警告] 后端服务已意外终止，退出码:", backend_process.poll())
                break
            if frontend_process.poll() is not None:
                print("\n[警告] 前端服务已意外终止，退出码:", frontend_process.poll())
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在捕获退出信号，清理后台服务进程...")
    finally:
        # 清理子进程
        try:
            print("正在终止后端服务...")
            backend_process.terminate()
            backend_process.wait(timeout=2)
        except Exception:
            pass
            
        try:
            print("正在终止前端服务...")
            frontend_process.terminate()
            frontend_process.wait(timeout=2)
        except Exception:
            pass
            
        print("所有服务清理完毕，感谢使用！")

if __name__ == "__main__":
    main()
