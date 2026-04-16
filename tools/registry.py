import subprocess
import os

class ToolBox:
    @staticmethod
    def write_file(path: str, content: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"✅ Successfully wrote to {path}"

    @staticmethod
    def run_command(command: str):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return f"✅ Output:\n{result.stdout}"
            else:
                return f"❌ Error:\n{result.stderr}"
        except Exception as e:
            return f"❌ Execution failed: {str(e)}"

    @staticmethod
    def list_files(path: str):
        return os.listdir(path)