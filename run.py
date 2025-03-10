import subprocess
def run_test_engine(file_path: str, file_ext: str) -> dict:
    try:
        if file_ext == ".json":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--format", "json"]
        elif file_ext == ".aasx":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path]
        elif file_ext == ".xml":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--format", "xml"]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        # stderr 확인 (예외 처리 필요)
        if result.stderr:
            return {"status": "Error", "details": result.stderr.strip()}
        else: 
        # stdout 확인
            if result.stdout:
                first_line = result.stdout.splitlines()[0]
                if "\033[92mCheck" in first_line:  # 초록색
                    return {"status": "Test Passed", "details": result.stdout.strip()}
                elif "\033[91mCheck" in first_line:
                    return {"status": "Test Failed", "details": result.stdout.strip()}
                else:
                    return {"Error"}
        return {"status": "Error", "details": "No output received from test engine."}
    except Exception as e:
        return {"status": "Error", "details": f"Unhandled Error: {str(e)}"}