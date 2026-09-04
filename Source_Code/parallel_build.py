import os
import sys
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

def run_command(cmd, cwd, name):
    print(f"  [开始] 任务: {name} (CWD: {cwd})")
    start_time = time.time()
    
    # 避开管道死锁：不拦截 stdout/stderr，直接流向当前终端输出。
    # 这样不仅能实时看到各编译器的输出，更能完全杜绝 OS 管道缓冲区被大量日志塞爆导致的永久死锁卡死。
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    
    elapsed = time.time() - start_time
    if result.returncode == 0:
        print(f"  [成功] 任务: {name} 已完成，耗时: {elapsed:.2f} 秒")
        return True, name, ""
    else:
        print(f"  [失败] 任务: {name} 失败，耗时: {elapsed:.2f} 秒！")
        return False, name, f"进程退出，返回码: {result.returncode}"

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    backend_dir = os.path.join(root_dir, "backend")

    print("=========================================================")
    print("   Hardware Engineering Toolbox - 前后端并行双通道构建工具")
    print("=========================================================")
    total_start = time.time()

    # 第一阶段：并行构建前端资源与 Python 后端 EXE
    tasks = [
        ("cmd /c \"npm run build\"", frontend_dir, "React 前端编译 (Vite + tsc)"),
        ("python package_backend.py", backend_dir, "Python 后端打包 (PyInstaller)")
    ]

    print("\n[第一步] 正在以多线程并行启动前端与后端构建服务...")
    success = True
    errors = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_command, cmd, cwd, name) for cmd, cwd, name in tasks]
        for future in futures:
            ok, name, err = future.result()
            if not ok:
                success = False
                errors.append((name, err))

    if not success:
        print("\n[错误] 构建中止！出现以下编译/打包错误：")
        for name, err in errors:
            print(f"\n--- {name} 错误详情 ---")
            print(err)
        sys.exit(1)

    # 第二阶段：串行执行 Electron 封包 (依赖前两步生成的静态资源与 backend.exe)
    print("\n[第二步] 前后端构建均已就绪。正在启动 Electron-Builder 进行桌面端封包...")
    ok, name, err = run_command("cmd /c \"set CSC_IDENTITY_AUTO_DISCOVERY=false && npm run dist\"", root_dir, "Electron 桌面免安装 EXE 封包")

    if ok:
        elapsed_total = time.time() - total_start
        print("\n=========================================================")
        print(f"  [完成] 平台并行构建成功！总耗时: {elapsed_total:.2f} 秒")
        print(f"  [输出] 目标文件: {os.path.join(root_dir, 'dist', 'Hardware Engineering Toolbox 1.0.0.exe')}")
        print("=========================================================")
    else:
        print(f"\n[错误] Electron 打包失败！\n{err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
