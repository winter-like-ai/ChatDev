import difflib
import os
import re
import subprocess

from chatdev.path_utils import get_workspace_root
from chatdev.utils import log_visualize


class Codes:
    def __init__(self, generated_content=""):
        self.directory: str = None
        self.version: float = 0.0
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
        code = "\n".join([line for line in code.split("\n") if len(line.strip()) > 0])
        return code

    def _update_codes(self, generated_content):
        """Merge newly generated markdown code blocks into the in-memory codebook."""
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

                log_visualize(update_codes_content)
                self.codebooks[key] = new_codes.codebooks[key]

    def _rewrite_codes(self, git_management, phase_info=None) -> None:
        """Write the current codebook to disk and optionally create git history."""
        directory = self.directory
        rewrite_codes_content = "**[Rewrite Codes]**\n\n"
        if os.path.exists(directory) and len(os.listdir(directory)) > 0:
            self.version += 1.0
        if not os.path.exists(directory):
            os.mkdir(self.directory)
            rewrite_codes_content += "{} Created\n".format(directory)

        for filename in self.codebooks.keys():
            filepath = os.path.join(directory, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as writer:
                writer.write(self.codebooks[filename])
                rewrite_codes_content += os.path.join(directory, filename) + " Wrote\n"

        if git_management:
            if not phase_info:
                phase_info = ""
            log_git_info = "**[Git Information]**\n\n"
            if self.version == 1.0:
                subprocess.run(["git", "init"], cwd=self.directory, check=False)
                log_git_info += "git init\n"
            subprocess.run(["git", "add", "."], cwd=self.directory, check=False)
            log_git_info += "git add .\n"

            # check if there exist diff
            completed_process = subprocess.run(
                ["git", "status"],
                cwd=self.directory,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if "nothing to commit" in completed_process.stdout:
                self.version -= 1.0
                return

            subprocess.run(
                ["git", "commit", "-m", f"v{self.version} {phase_info}"],
                cwd=self.directory,
                check=False,
            )
            log_git_info += "git commit -m \"v{}\"\n".format(str(self.version) + " " + phase_info)
            if self.version == 1.0:
                workspace_root = get_workspace_root()
                workspace_relative_path = os.path.join(os.path.basename(workspace_root), os.path.basename(self.directory))
                subprocess.run(
                    ["git", "submodule", "add", f"./{workspace_relative_path}", workspace_relative_path],
                    cwd=os.path.dirname(os.path.dirname(self.directory)),
                    check=False,
                )
                log_git_info += "git submodule add ./{} {}\n".format(
                    workspace_relative_path,
                    workspace_relative_path,
                )
                log_visualize(rewrite_codes_content)
            log_visualize(log_git_info)

    def _get_codes(self) -> str:
        """Return every tracked file as a single markdown-formatted string."""
        content = ""
        for filename in self.codebooks.keys():
            content += "{}\n```{}\n{}\n```\n\n".format(filename,
                                                       "python" if filename.endswith(".py") else filename.split(".")[
                                                           -1], self.codebooks[filename])
        return content

    def _load_from_hardware(self, directory) -> None:
        """Load existing Python files from a base directory into the codebook."""
        assert any(
            filename.endswith(".py")
            for _, _, filenames in os.walk(directory)
            for filename in filenames
        )
        for root, directories, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(".py"):
                    source_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(source_path, directory)
                    code = open(source_path, "r", encoding="utf-8").read()
                    self.codebooks[relative_path] = self._format_code(code)
        log_visualize("{} files read from {}".format(len(self.codebooks.keys()), directory))
