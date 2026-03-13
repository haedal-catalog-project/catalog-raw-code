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
    
    # 핵심 1: 초보자의 파이썬 파일을 백그라운드에서 실행!
    # "-u" 옵션은 print() 결과를 지연 없이 즉시 웹으로 보내기 위해 필수입니다.
    process = await asyncio.create_subprocess_exec(
        "uv", "run", "python", "-u", "student_code.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # 핵심 2: 파이썬의 print() 결과를 읽어서 웹(xterm.js)으로 전송
    async def read_stdout():
        while True:
            # 글자가 나오는 대로 즉시 읽음
            data = await process.stdout.read(1024)
            if not data:
                break
            # 줄바꿈(\n)을 xterm.js 형식(\r\n)으로 변환해서 전송
            text = data.decode("utf-8", errors="replace").replace('\n', '\r\n')
            await websocket.send_text(text)

    # 핵심 3: 웹에서 친 키보드 입력을 파이썬의 input()으로 전달
    async def write_stdin():
        try:
            while True:
                data = await websocket.receive_text()
                # 사용자가 웹에서 엔터를 치면 파이썬으로 전달
                process.stdin.write(data.encode("utf-8"))
                await process.stdin.drain()
        except WebSocketDisconnect:
            pass

    # 두 작업을 동시에 실행
    task_out = asyncio.create_task(read_stdout())
    task_in = asyncio.create_task(write_stdin())

    # 파이썬 코드가 끝날 때까지 대기
    await process.wait()
    
    # 종료되면 연결 정리
    task_out.cancel()
    task_in.cancel()
    await websocket.send_text("\r\n[프로그램이 종료되었습니다 - 다시 사용하려면 새로고침 해주세요]\r\n")
    await websocket.close()
