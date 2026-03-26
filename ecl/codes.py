import difflib
import os
import re
import subprocess
import shutil
import time
import signal
from utils import get_easyDict_from_filepath


class Codes:
    def __init__(self, generated_content=""):
        """初始化 Codes 实例，从配置中读取路径，解析生成的代码内容。"""
        cfg = get_easyDict_from_filepath("./ecl/config.yaml")
        self.directory: str = cfg.codes.tmp_directory
        self.main_script: str = cfg.codes.main_script
        self.generated_content: str = generated_content
        self.codebooks = {}

        def extract_filename_from_line(lines):
            file_name = ""
            for candidate in re.finditer(r"(\w+\.\w+)", lines, re.DOTALL):
                file_name = candidate.group()
                file_name = file_name.lower()
            return file_name

        def extract_filename_from_code(code):
            file_name = ""
            regex_extract = r"class (\S+?):\n"
            matches_extract = re.finditer(regex_extract, code, re.DOTALL)
            for match_extract in matches_extract:
                file_name = match_extract.group(1)
            file_name = file_name.lower().split("(")[0] + ".py"
            return file_name

        if generated_content != "":
            regex = r"(.+?)\n```.*?\n(.*?)```"
            matches = re.finditer(regex, self.generated_content, re.DOTALL)
            for match in matches:
                code = match.group(2)
                if "CODE" in code:
                    continue
                group1 = match.group(1)
                filename = extract_filename_from_line(group1)
                if "__main__" in code:
                    filename = "main.py"
                if filename == "":  # post-processing
                    filename = extract_filename_from_code(code)
                assert filename != ""
                if filename is not None and code is not None and len(filename) > 0 and len(code) > 0:
                    self.codebooks[filename] = self._format_code(code)

    def _format_code(self, code):
        """格式化代码，移除空行。"""
        code = "\n".join([line for line in code.split("\n") if len(line.strip()) > 0])
        return code

    def _update_codes(self, generated_content):
        """对比并更新代码。如果有变更，则生成 diff 并在终端或日志中记录。"""
        new_codes = Codes(generated_content)
        differ = difflib.Differ()
        for key in new_codes.codebooks.keys():
            if key not in self.codebooks.keys() or self.codebooks[key] != new_codes.codebooks[key]:
                update_codes_content = "**[Update Codes]**\n\n"
                update_codes_content += "{} updated.\n".format(key)
                old_codes_content = self.codebooks[key] if key in self.codebooks.keys() else "# None"
                new_codes_content = new_codes.codebooks[key]

                lines_old = old_codes_content.splitlines()
                lines_new = new_codes_content.splitlines()

                unified_diff = difflib.unified_diff(lines_old, lines_new, lineterm='', fromfile='Old', tofile='New')
                unified_diff = '\n'.join(unified_diff)
                update_codes_content = update_codes_content + "\n\n" + """```
'''

'''\n""" + unified_diff + "\n```"

                self.codebooks[key] = new_codes.codebooks[key]

    def _rewrite_codes(self) -> None:
        """重新创建工作目录并将所有代码写入本地系统。"""
        directory = self.directory
        rewrite_codes_content = "**[Rewrite Codes]**\n"
        if os.path.exists(directory):
            shutil.rmtree(self.directory)
        if not os.path.exists(directory):
            os.mkdir(self.directory)
            rewrite_codes_content += "{} Created\n".format(directory)

        for filename in self.codebooks.keys():
            filepath = os.path.join(directory, filename)
            with open(filepath, "w", encoding="utf-8") as writer:
                writer.write(self.codebooks[filename])
                rewrite_codes_content += os.path.join(directory, filename) + " Wrote\n"
        # print(rewrite_codes_content)

    def _run_codes(self) -> None:
        """运行 main 脚本以验证代码是否可执行并返回错误状态及信息。"""
        directory = os.path.abspath(self.directory)
        if self.main_script not in os.listdir(directory):
            return False, "{} Not Found".format(self.main_script)

        success_info = "The software run successfully without errors."

        try:
            # check if we are on windows or linux
            if os.name == 'nt':
                command = "cd {} && dir && python {}".format(directory, self.main_script)
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                command = "cd {}; ls -l; python3 {};".format(directory, self.main_script)
                process = subprocess.Popen(command,
                                           shell=True,
                                           preexec_fn=os.setsid,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE
                                           )
            time.sleep(3)
            return_code = process.returncode
            # Check if the software is still running
            if process.poll() is None:
                if "killpg" in dir(os):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    os.kill(process.pid, signal.SIGTERM)
                    if process.poll() is None:
                        os.kill(process.pid, signal.CTRL_BREAK_EVENT)

            if return_code == 0:
                return False, success_info
            else:
                error_output = process.stderr.read().decode('utf-8')
                if error_output:
                    if "Traceback".lower() in error_output.lower():
                        errs = error_output.replace(directory + "/", "")
                        return True, errs
                else:
                    return False, success_info
        except subprocess.CalledProcessError as e:
            return True, f"Error: {e}"
        except Exception as ex:
            return True, f"An error occurred: {ex}"

        return False, success_info

    def _get_codes(self) -> str:
        """把所有被管理的文件内容组装成 Markdown 格式的字符串。"""
        content = ""
        for filename in self.codebooks.keys():
            content += "{}\n```{}\n{}\n```\n\n".format(filename,
                                                       "python" if filename.endswith(".py") else filename.split(".")[
                                                           -1], self.codebooks[filename])
        return content

    def _load_from_hardware(self, directory) -> None:
        """从指定文件夹载入已存在的代码文件到缓存中。"""
        assert len([filename for filename in os.listdir(directory) if filename.endswith(".py")]) > 0
        for root, directories, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(".py"):
                    code = open(os.path.join(directory, filename), "r", encoding="utf-8").read()
                    self.codebooks[filename] = self._format_code(code)
        print("{} files read from {}".format(len(self.codebooks.keys()), directory))
