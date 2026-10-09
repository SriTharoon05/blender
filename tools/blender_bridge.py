"""Local client for the installed Blender MCP add-on. All scripts stay in project."""
import json, socket, sys
from pathlib import Path

def call(code):
    with socket.create_connection(('127.0.0.1', 9876), timeout=15) as s:
        s.settimeout(900)
        s.sendall(json.dumps({'type':'execute_code','params':{'code':code}}).encode())
        buf=b''
        while True:
            chunk=s.recv(65536)
            if not chunk: raise RuntimeError('Blender disconnected')
            buf+=chunk
            try: return json.loads(buf)
            except (json.JSONDecodeError, UnicodeDecodeError): pass

if __name__=='__main__':
    code=Path(sys.argv[1]).read_text(encoding='utf-8') if len(sys.argv)>1 else sys.stdin.read()
    result=call(code)
    print(json.dumps(result,indent=2))
    if result.get('status')!='success': sys.exit(1)
