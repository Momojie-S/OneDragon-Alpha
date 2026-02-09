import json
import os
from enum import StrEnum
from typing import Annotated, Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_alpha.server.dependencies import ContextDep
from one_dragon_alpha.session.session import Session

router = APIRouter(prefix="/chat")


async def get_db_session() -> AsyncSession:
    """获取数据库会话依赖.

    Yields:
        AsyncSession: 数据库会话

    Raises:
        HTTPException: 如果无法获取数据库会话
    """
    from one_dragon_alpha.services.mysql import MySQLConnectionService

    try:
        # 获取 MySQL 连接服务实例
        mysql_service = MySQLConnectionService()
        async with await mysql_service.get_session() as session:
            yield session
    except Exception as e:
        from one_dragon_agent.core.system.log import get_logger

        logger = get_logger(__name__)
        logger.error(f"无法获取数据库会话: {e}")
        raise HTTPException(
            status_code=500,
            detail="无法连接到数据库",
        ) from e


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


class ChatRequest(BaseModel):
    """Request model for chat operations.

    Attributes:
        session_id: Unique identifier for chat session.
                   Optional - if not provided, a new session will be created.
        user_input: The user's message content.
        model_config_id: Model configuration ID to use for this request.
        model_id: Model ID within the configuration to use.
    """
    session_id: str | None = None
    user_input: str
    model_config_id: int
    model_id: str


class GetAnalysisRequest(BaseModel):
    """Request model for getting analysis results.

    Attributes:
        session_id: Unique identifier for chat session.
        analyse_id: Analysis ID to retrieve results for.
    """
    session_id: str
    analyse_id: int


class ChatResponseType(StrEnum):
    """Enumeration of chat response types.

    This enum defines different types of responses that can be sent
    during chat operations.

    Attributes:
        MESSAGE_UPDATE: Partial response sent incrementally for streaming. (SSE/WebSocket).
        MESSAGE_COMPLETED: Final chunk of a message of response (SSE/WebSocket).
                         Used to indicate completion of a logical message that may contain
                         multiple messages (text, tool calls, tool results).
        RESPONSE_COMPLETED: Final chunk of whole response (SSE/WebSocket).
                           Used to indicate completion of entire response.
        STATUS: Status update message.
        ERROR: Error response message.
    """

    MESSAGE_UPDATE = "message_update"  # Message update package (SSE/WebSocket)
    MESSAGE_COMPLETED = "message_completed"  # Final chunk of a message (SSE/WebSocket)
    RESPONSE_COMPLETED = "response_completed"  # Final chunk of whole response (SSE/WebSocket)
    STATUS = "status"  # Status update (WebSocket)
    ERROR = "error"  # Error response (all channels)


class ChatResponse(BaseModel):
    """Response model for chat operations.

    Attributes:
        session_id: Unique identifier for chat session.
        type: Type of response message.
        message: Response message as a dictionary.
    """
    session_id: str
    type: str  # ChatResponseType
    message: dict[str, Any]


def get_session(context: ContextDep, session_id: str | None) -> tuple[str, Session]:
    """Helper function to get or create session and retrieve session object.

    This function centralizes session management logic for all chat endpoints.
    If session_id is None, creates a new session. If session_id is provided,
    validates that session exists. This ensures consistent session handling
    across all communication modes.

    Args:
        context: Dependency context providing services.
        session_id: Optional session ID. If None, creates new session.

    Returns:
        Tuple of (session_id, session) where session is guaranteed to exist.

    Raises:
        HTTPException: If session_id is provided but session does not exist (404).
    """
    # Get or create session ID
    if session_id is None:
        # Create new session if not provided
        session_id = context.session_service.create_session()

    # Retrieve session from session service (don't create if not exists)
    session = context.session_service.get_session(session_id)

    # Check if session exists when client provided session_id
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return session_id, session


async def stream_response_generator(
    session_id: str,
    session: Session,
    user_input: str,
    model_config_id: int,
    model_id: str,
    config,
    context: ContextDep,
) -> AsyncGenerator[str, None]:
    """Generate streaming response chunks.

    This generator creates Server-Sent Events (SSE) format responses
    for real-time chat streaming by delegating to the Session object.

    Args:
        session_id: Unique identifier for chat session.
        session: Session instance for processing chat message.
        user_input: The user's message content.
        model_config_id: Model configuration ID.
        model_id: Model ID within the configuration.
        config: Model configuration object.
        context: Dependency context providing services.

    Yields:
        SSE-formatted response chunks.
    """
    try:
        async for session_message in session.chat(user_input, model_config_id, model_id, config):
            response_type = ChatResponseType.RESPONSE_COMPLETED if session_message.response_completed else (
                ChatResponseType.MESSAGE_COMPLETED if session_message.message_completed else ChatResponseType.MESSAGE_UPDATE
            )
            response = ChatResponse(
                type=response_type,
                session_id=session_id,
                message={} if session_message.msg is None else session_message.msg.to_dict(),
            )
            yield f"data: {response.model_dump_json()}\n\n"
    except Exception as e:
        response = ChatResponse(
            type=ChatResponseType.ERROR,
            session_id=session_id,
            message={"hint": str(e)},
        )
        yield f"data: {response.model_dump_json()}\n\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest, session: SessionDep, context: ContextDep) -> StreamingResponse:
    """Process a chat message and return streaming response.

    This endpoint provides a streaming interface for chat operations.
    Responses are sent incrementally as they are generated.
    Note: Each chunk contains complete current message (cumulative).

    Args:
        request: Chat request containing session ID, user input, model_config_id, and model_id.
        session: Database session for validating model configuration.
        context: Dependency context providing services.

    Returns:
        Streaming response with SSE format.

    Raises:
        HTTPException: If model configuration is invalid or not found.
    """
    # 导入 ModelConfigService
    from one_dragon_agent.core.model.service import ModelConfigService

    # 验证模型配置并获取完整配置(包含 api_key)
    service = ModelConfigService(session)
    try:
        config = await service.get_model_config_internal(request.model_config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    # 验证配置是否启用
    if not config.is_active:
        raise HTTPException(status_code=400, detail=f"模型配置 '{config.name}' 已禁用")

    # 验证 model_id 是否在配置中
    model_ids = [m.model_id for m in config.models]
    if request.model_id not in model_ids:
        raise HTTPException(
            status_code=400,
            detail=f"模型 ID '{request.model_id}' 不在配置 '{config.name}' 中。可用模型: {model_ids}",
        )

    # 获取或创建 Session
    session_id, tushare_session = get_session(context, request.session_id)

    return StreamingResponse(
        stream_response_generator(
            session_id=session_id,
            session=tushare_session,
            user_input=request.user_input,
            model_config_id=request.model_config_id,
            model_id=request.model_id,
            config=config,
            context=context,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/get_analyse_by_code_result")
async def get_analyse_by_code_result(request: GetAnalysisRequest, context: ContextDep) -> dict[str, Any]:
    """Get analysis results by session ID and analysis ID.

    This endpoint retrieves the analysis results stored in the workspace
    directory for a specific session and analysis ID combination.

    Args:
        request: Request containing session_id and analyse_id.
        context: Dependency context providing services.

    Returns:
        Dictionary containing the analysis results or error message.

    Raises:
        HTTPException: If session not found, analysis directory not found,
                       or result file not found.
    """
    # Validate session exists
    session = context.session_service.get_session(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {request.session_id}")

    # Get workspace directory from environment
    workspace_dir = os.getenv("WORKSPACE_DIR")
    if not workspace_dir:
        raise HTTPException(status_code=500, detail="WORKSPACE_DIR environment variable not set")

    # Construct analysis directory path
    analyse_dir = os.path.join(workspace_dir, "analyse_by_code", f"{request.session_id}-{request.analyse_id}")

    # Check if analysis directory exists
    if not os.path.exists(analyse_dir):
        raise HTTPException(status_code=404, detail=f"Analysis directory not found: {request.analyse_id}")

    # Check if result.json file exists
    result_file = os.path.join(analyse_dir, "result.json")
    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail=f"Result file not found for analysis: {request.analyse_id}")

    try:
        # Read and return the result.json file
        with open(result_file, "r", encoding="utf-8") as f:
            result_data = json.load(f)

        return {
            "session_id": request.session_id,
            "analyse_id": request.analyse_id,
            "result": result_data
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in result file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading result file: {str(e)}")
