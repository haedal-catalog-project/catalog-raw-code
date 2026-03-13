import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    process = None
    try:
        # 파이썬 실행 (이전과 동일)
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "python", "-u", "student_code.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async def read_stdout():
            while True:
                data = await process.stdout.read(1024)
                if not data:
                    break
                text = data.decode("utf-8", errors="replace").replace('\n', '\r\n')
                await websocket.send_text(text)

        async def write_stdin():
            while True:
                # 글자 수 제한 (버퍼 오버플로우 방지: 한 번에 1000자까지만 허용)
                data = await websocket.receive_text()
                if len(data) > 1000:
                    data = data[:1000] 
                
                if process and process.stdin:
                    process.stdin.write(data.encode("utf-8"))
                    await process.stdin.drain()

        task_out = asyncio.create_task(read_stdout())
        task_in = asyncio.create_task(write_stdin())

        # ⭐️ 안전장치 1: Timeout 설정 (예: 60초 안에 코드가 안 끝나면 강제 종료)
        try:
            await asyncio.wait_for(process.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            if process:
                process.kill() # 자비 없이 프로세스를 죽임
            await websocket.send_text("\r\n\x1b[31m[경고] 실행 시간(60초)이 초과되어 강제 종료되었습니다.\x1b[0m\r\n")

        task_out.cancel()
        task_in.cancel()
        await websocket.send_text("\r\n[프로그램이 종료되었습니다]\r\n")
        
    except WebSocketDisconnect:
        # ⭐️ 안전장치 2: 사용자가 도중에 창을 닫거나 나갔을 때
        print("사용자가 웹 연결을 끊었습니다.")
    finally:
        # ⭐️ 안전장치 3: 어떤 오류가 나더라도 실행 중인 파이썬 찌꺼기를 확실히 제거
        if process and process.returncode is None:
            try:
                process.kill()
                print("남아있는 파이썬 프로세스를 강제 종료했습니다.")
            except ProcessLookupError:
                pass
