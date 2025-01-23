import subprocess

def run_test_engine_returncode(file_path: str, file_ext: str) -> dict:
    """AAS Test Engine을 실행하고 결과를 반환"""
    try:
        if file_ext == ".json":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--format", "json"]
        elif file_ext == ".aasx":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path]
        elif file_ext == ".xml":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--format", "xml"]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            return {"status": "Test Passed", "details": result.stdout.strip()}
        else:
            return {"status": "Test Failed", "details": result.stdout.strip()}
    except Exception as e:
        return {"status": "Cannot test the file", "details": f"Unhandled Error: {str(e)}"}