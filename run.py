import json
import subprocess
from utils.error_handler import ErrorCode

def run_test_engine(file_path: str, file_ext: str) -> dict:
    try:
        if file_ext == ".json":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--format", "json", "--output", "json"]
        elif file_ext == ".aasx":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--output", "json"]
        elif file_ext == ".xml":
            command = ["python", "-m", "aas_test_engines", "check_file", file_path, "--format", "xml", "--output", "json"]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
    #에러처리 공통 함수로 처리

        # stderr 확인 (예외 처리 필요)
        if result.stderr:
            jsonOutput = json.loads(result.stderr)
            # return {"status": "Error", "details": result.stderr.strip()}
            return jsonOutput
        else: 
        # stdout 확인
            if result.stdout:
                try:
                    jsonOutput = json.loads(result.stdout)
                    # return {}
                except json.JSONDecodeError:
                    return {"status": "Error", "details": jsonOutput}
                first_line = result.stdout.splitlines()[0]
                if "\033[92mCheck" in first_line:  # 초록색
                    return {"status": "Test Passed", "details": jsonOutput}
                elif "\033[91mCheck" in first_line:
                    return {"status": "Test Failed", "details": jsonOutput}
                else:
                    return {"status": "json output", "details": jsonOutput}
        return {"status": "Error", "details": "No output received from test engine."}
    
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON decode error in output: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unhandled Error: {str(e)}")