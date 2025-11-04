# app/api/events_sse.py
# SSE endpoint for kiosks. Push-only (server -> client) event stream.
# Auth via your existing kiosk JWT dependency.
#
# Notes:
# - Native EventSource cannot set Authorization header. If you use plain
#   EventSource in the browser, consider: (a) cookie-based auth, or
#   (b) a tiny EventSource polyfill that adds the header, or
#   (c) later we can add a `?token=` fallback here.
# - We send heartbeat comments (": ping") every 15s to keep proxies/load
#   balancers from closing the idle connection.
# - Each message is JSON encoded and sent as a standard SSE "data:" frame.

import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from ..auth.kiosk_dependencies import get_current_kiosk_token_data
from ..auth.kiosk_auth_service import kiosk_auth_service
from ..database.models import User
from ..database.connection import get_db
from sqlalchemy.orm import Session
from ..websockets.event_bus import bus

router = APIRouter(prefix="/kiosk", tags=["Kiosk Events"])


async def get_kiosk_user_from_query_token(
    token: Optional[str] = Query(None, description="JWT access token for SSE authentication"),
    db: Session = Depends(get_db)
) -> User:
    """
    Get kiosk user from token in query parameter (for SSE connections).
    EventSource doesn't support custom headers, so we accept token as query param.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token in query parameter",
        )

    # Verify the token using existing kiosk auth service
    token_data = kiosk_auth_service.verify_kiosk_token(token)

    # Get user from database
    user = kiosk_auth_service.get_kiosk_user_by_id(db, token_data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kiosk user not found or invalid",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kiosk user account is inactive",
        )

    return user


@router.get("/events")
async def kiosk_events_sse(
    request: Request,
    current_user: User = Depends(get_kiosk_user_from_query_token),
):
    """
    Long-lived SSE connection for a kiosk.
    We route events by kiosk username (unique per kiosk account).

    Client usage example (with header-capable polyfill):
        const es = new EventSourcePolyfill('/api/kiosk/events', {
          headers: { Authorization: 'Bearer <JWT>' }
        });
        es.onmessage = (ev) => { const msg = JSON.parse(ev.data); ... };

    IMPORTANT:
    - This endpoint never completes under normal conditions.
    - Client should auto-reconnect on network errors.
    """
    kiosk_username = current_user.username
    print(f"🔌 SSE: New connection from kiosk '{kiosk_username}'")

    async def event_stream():
        # Send initial retry hint
        print(f"🎬 SSE: Starting event_stream() for kiosk '{kiosk_username}'")
        yield b"retry: 3000\n\n"
        print(f"✅ SSE: Sent initial retry hint to kiosk '{kiosk_username}'")

        # Create a simple queue for this connection
        event_queue = asyncio.Queue(maxsize=100)

        # Subscribe to broadcast channel
        async def event_listener():
            try:
                print(f"🎧 SSE: Event listener starting for kiosk '{kiosk_username}'")
                async for event in bus.subscribe("kiosk_broadcast"):
                    print(f"🎯 SSE: Event listener received event for kiosk '{kiosk_username}': {event}")
                    try:
                        await event_queue.put(event)
                    except asyncio.QueueFull:
                        # Remove oldest event and add new one
                        try:
                            event_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                        await event_queue.put(event)
                print(f"🛑 SSE: Event listener loop ended for kiosk '{kiosk_username}'")
            except Exception as e:
                print(f"❌ SSE: Event listener error for kiosk '{kiosk_username}': {e}")
                import traceback
                traceback.print_exc()

        # Start the event listener task
        listener_task = asyncio.create_task(event_listener())
        print(f"🔧 SSE: Event listener task created for kiosk '{kiosk_username}'")

        try:
            print(f"🚀 SSE: Event stream started for kiosk '{kiosk_username}'")
            
            while True:
                try:
                    # Wait for either an event or timeout (for heartbeat)
                    event = await asyncio.wait_for(event_queue.get(), timeout=15.0)
                    
                    # Send the event
                    print(f"📤 SSE: Sending event to kiosk '{kiosk_username}': {event}")
                    payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
                    yield b"data: " + payload + b"\n\n"
                    
                except asyncio.TimeoutError:
                    # Send heartbeat as a data message so frontend can detect it
                    print(f"💓 SSE: Sending heartbeat to kiosk '{kiosk_username}'")
                    heartbeat_payload = json.dumps({"event_type": "HEARTBEAT"}, ensure_ascii=False).encode("utf-8")
                    yield b"data: " + heartbeat_payload + b"\n\n"
                    
                except Exception as e:
                    print(f"❌ SSE: Error in event processing for kiosk '{kiosk_username}': {e}")
                    break
                
                # Check if client disconnected
                if await request.is_disconnected():
                    print(f"🔌 SSE: Client disconnected for kiosk '{kiosk_username}'")
                    break
                    
        except Exception as e:
            print(f"❌ SSE: Stream error for kiosk '{kiosk_username}': {e}")
        finally:
            # Clean up
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
            print(f"🔌 SSE: Connection closed for kiosk '{kiosk_username}'")

    headers = {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # If you run behind nginx, consider:  "X-Accel-Buffering": "no"
    }
    return StreamingResponse(event_stream(), headers=headers)