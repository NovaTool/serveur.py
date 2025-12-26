from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.json
    code = data.get('code')
    print(f"Executing: {code}")
    
    # Danger: eval/exec can be risky. For now, we'll just print or run specific commands.
    # If the user wants to run a python command:
    try:
        # Capture output
        result = subprocess.check_output(code, shell=True, text=True)
        return {"status": "success", "output": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == '__main__':
    app.run(port=5000)
