import os
import sys
import subprocess

def check_requirements():
    print("Checking and installing requirements...")
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found, installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "matplotlib", "numpy", "PyQt5"])

def build_executable():
    check_requirements()
    
    # 自动在打包前生成最新模块的静态导入注册表
    try:
        from tools.generate_registry import generate
        generate()
    except Exception as e:
        print(f"Error generating static registry: {e}")
        return
        
    app_name = "Circuit_Calculator_Pro"
    main_script = "main.py"
    
    print(f"\n=========================================================")
    print(f"Starting packaging for {app_name}...")
    print(f"=========================================================\n")
    
    # Optional files to include if they exist
    data_files = [
        "cmd_buttons.json",
        "app_config.json"
    ]
    
    # Base PyInstaller command
    command = [
        "pyinstaller",
        "--noconfirm",         # Replace existing build/dist folders
        "--onefile",           # Create a single file executable
        "--windowed",          # Hide console window
        "--log-level=INFO",
        f"--name={app_name}",
        "--clean",
    ]
    
    # 增加子模块搜索路径，确保 PyInstaller 能解析子目录里的平铺导入关系并打包
    for folder in ['magnetics', 'power', 'control', 'signal', 'physical']:
        command.extend(["--paths", os.path.join("modules", folder)])
    command.extend(["--paths", "."])
    
    # Add optional data files dynamically if they exist in the current directory
    for file in data_files:
        if os.path.exists(file):
            print(f"Found optional data file: {file}, adding to build.")
            # Format depends on OS: Windows uses ';' and Linux/Mac uses ':'
            separator = ";" if sys.platform.startswith("win") else ":"
            command.extend(["--add-data", f"{file}{separator}."])
        else:
            print(f"Optional data file '{file}' not found, skipping.")

    # Finally add the main script
    command.append(main_script)
    
    print(f"\n[INFO] Running PyInstaller command:\n{' '.join(command)}\n")
    print("This may take a few minutes. Please wait...")
    
    try:
        subprocess.check_call(command)
        print(f"\nPackaged Successfully!")
        print(f"Your executable output is ready in the 'dist' folder.")
        print(f"Executable full path: dist\\{app_name}.exe")
        print("Note: The first launch might take a few moments to load packages like matplotlib.")
    except subprocess.CalledProcessError as e:
        print("\nBuild failed. Please check the logs above for details.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        
if __name__ == "__main__":
    build_executable()
    
    # Keep console open in Windows so user can read output when double-clicking
    if sys.platform.startswith("win"):
        input("\nPress Enter to exit...")
