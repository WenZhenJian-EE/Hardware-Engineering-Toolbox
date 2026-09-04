import os
import sys
import subprocess
import shutil

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    print("=========================================================")
    print("      Hardware Engineering Toolbox - 后端 PyInstaller 打包  ")
    print("=========================================================")

    # 1. 确保 pyinstaller 可用
    try:
        import PyInstaller
        print("  => PyInstaller 已就绪。")
    except ImportError:
        print("  => 未检测到 PyInstaller，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # 2. 清理旧构建目录
    build_dir = os.path.join(backend_dir, "build")
    dist_dir = os.path.join(backend_dir, "dist")
    spec_file = os.path.join(backend_dir, "backend.spec")

    for p in [build_dir, dist_dir, spec_file]:
        if os.path.exists(p):
            print(f"  => 正在清理旧文件/目录: {os.path.basename(p)}")
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)

    # 3. 构造 PyInstaller 命令行参数
    # Windows 分隔符为 ';', Unix 为 ':'
    sep = ";" if os.name == "nt" else ":"
    
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--onedir",
        "--name", "backend",
        f"--add-data=data{sep}data",
        f"--add-data=database.py{sep}.",
        f"--add-data=formula.py{sep}.",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=formula",
        "--hidden-import=database",
        "--hidden-import=sqlite3",
        "app.py"
    ]

    print(f"\n执行打包命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, shell=True)

    if result.returncode == 0:
        print("\n  => 后端打包成功！")
        executable_path = os.path.join(dist_dir, "backend", "backend.exe" if os.name == "nt" else "backend")
        print(f"  => 生成的可执行程序路径: {executable_path}")
    else:
        print("\n  ❌ 后端打包失败！")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
