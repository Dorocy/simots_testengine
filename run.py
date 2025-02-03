import subprocess
import re

def run_test_engine_color(file_path: str, file_ext: str) -> dict:
    try:
        if file_ext == ".aasx":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path]
        elif file_ext == ".json":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--format", "json"]
        elif file_ext == ".xml":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--format", "xml"]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.stderr:
            return {"status": "Error", "details": result.stderr.strip()}

        if result.stdout:
            output_lines = result.stdout.splitlines()

            if file_ext == ".aasx":
                # ANSI 색상 코드가 포함된 "Check"만 찾는 정규식 패턴 (Checking 제외)
                check_pattern = re.compile(r"\x1b\[\d{2}mCheck\b")

                # "Check" 단어가 포함된 첫 번째 줄 찾기
                check_start_index = next((i for i, line in enumerate(output_lines) if check_pattern.search(line)), len(output_lines))

                # 해당 줄 이후의 내용만 유지
                filtered_output = "\n".join(output_lines[check_start_index:]).strip()
            else:
                filtered_output = result.stdout.strip()

            return {
                "status": "Test Passed" if "\033[92mCheck" in filtered_output else "Test Failed",
                "details": filtered_output
            }

        return {"status": "Error", "details": "No output received from test engine."}
    except Exception as e:
        return {"status": "Error", "details": f"Unhandled Error: {str(e)}"}