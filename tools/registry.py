import subprocess
import os
from core.logger import setup_logger

logger = setup_logger("Toolbox")

class ToolBox:
    @staticmethod
    def write_file(path: str, content: str):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            logger.info(f"File written successfully to {path} ({len(content)} bytes)")
            return f"✅ Successfully wrote to {path}"
        except Exception as e:
            logger.error(f"Failed to write file to {path}: {str(e)}")
            return f"❌ Write failed: {str(e)}"

    @staticmethod
    def run_command(command: str):
        logger.info(f"Executing system command: '{command}'")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.debug(f"Command success. Output: {result.stdout[:100]}...")
                return f"✅ Output:\n{result.stdout}"
            else:
                logger.error(f"Command failed with code {result.returncode}. Error: {result.stderr}")
                return f"❌ Error:\n{result.stderr}"
        except Exception as e:
            logger.error(f"System command execution failed: {str(e)}")
            return f"❌ Execution failed: {str(e)}"

    @staticmethod
    def list_files(path: str):
        logger.debug(f"Listing files in {path}")
        try:
            files = os.listdir(path)
            logger.info(f"Found {len(files)} files/folders in directory.")
            return files
        except Exception as e:
            logger.error(f"Failed to list files in {path}: {str(e)}")
            return []