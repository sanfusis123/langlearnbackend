from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.db.database import connect_to_mongo, close_mongo_connection
from app.api.websockets.conversation import websocket_conversation_endpoint
from app.core.logging_config import setup_logging

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== APPLICATION STARTUP ===")
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info("Connecting to MongoDB...")
    await connect_to_mongo()
    logger.info("MongoDB connected successfully")
    logger.info("=========================")
    yield
    logger.info("=== APPLICATION SHUTDOWN ===")
    await close_mongo_connection()
    logger.info("MongoDB connection closed")
    logger.info("===========================")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"^https?://localhost:.*",
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Chat Application", "version": settings.VERSION}


@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    print(f"TEST WebSocket connection attempt")
    await websocket.accept()
    try:
        await websocket.send_text("Hello from WebSocket!")
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print(f"TEST WebSocket error: {e}")

@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    print(f"WebSocket connection attempt to /ws/conversation")
    print(f"Query params: {websocket.query_params}")
    
    # Get query parameters from the WebSocket request
    token = websocket.query_params.get("token")
    language = websocket.query_params.get("language", "en")
    session_id = websocket.query_params.get("session_id", None)
    scenario_id = websocket.query_params.get("scenario_id", None)
    scenario_type = websocket.query_params.get("scenario_type", None)
    
    print(f"Token: {token[:20] if token else 'None'}..., Language: {language}")
    print(f"Session ID: {session_id}, Scenario ID: {scenario_id}, Scenario Type: {scenario_type}")
    
    try:
        await websocket_conversation_endpoint(
            websocket, 
            token=token, 
            language=language, 
            session_id=session_id,
            scenario_id=scenario_id,
            scenario_type=scenario_type
        )
    except Exception as e:
        print(f"WebSocket error in main: {e}")
        import traceback
        traceback.print_exc()
        try:
            if websocket.client_state.value != 3:  # Not already closed
                await websocket.close(code=1011, reason=f"Server error: {str(e)}")
        except:
            pass