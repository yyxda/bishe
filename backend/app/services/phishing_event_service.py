"""钓鱼检测事件推送服务。

通过SSE向前端推送钓鱼检测结果的增量更新事件。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional


class PhishingEventService:
    """钓鱼检测事件推送服务。

    维护每个用户的SSE连接队列，并支持发送检测结果更新事件。
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """初始化事件推送服务。

        Args:
            logger: 日志记录器。
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._connections: Dict[int, List[asyncio.Queue[str]]] = {}
        self._lock = asyncio.Lock()

    async def register(self, user_id: int) -> asyncio.Queue[str]:
        """注册用户SSE连接。

        Args:
            user_id: 用户ID。

        Returns:
            推送队列。
        """
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._connections.setdefault(user_id, []).append(queue)
            self._logger.info(
                "SSE连接注册: user_id=%s, total=%d",
                user_id,
                len(self._connections[user_id]),
            )
        return queue

    async def unregister(self, user_id: int, queue: asyncio.Queue[str]) -> None:
        """注销用户SSE连接。

        Args:
            user_id: 用户ID。
            queue: 推送队列。
        """
        async with self._lock:
            queues = self._connections.get(user_id, [])
            if queue in queues:
                queues.remove(queue)
            if not queues:
                self._connections.pop(user_id, None)
            self._logger.info("SSE连接注销: user_id=%s", user_id)

    async def publish_detection_update(self, user_id: int, payload: Dict[str, Any]) -> None:
        """推送检测结果更新事件。

        Args:
            user_id: 用户ID。
            payload: 事件数据。
        """
        message = self._format_sse("phishing_update", payload)
        await self._broadcast(user_id, message)

    async def publish_batch_completed(self, user_id: int, payload: Dict[str, Any]) -> None:
        """推送批量检测完成事件。

        Args:
            user_id: 用户ID。
            payload: 事件数据。
        """
        message = self._format_sse("phishing_batch_completed", payload)
        await self._broadcast(user_id, message)

    async def _broadcast(self, user_id: int, message: str) -> None:
        """向指定用户广播事件。

        Args:
            user_id: 用户ID。
            message: SSE消息。
        """
        async with self._lock:
            queues = list(self._connections.get(user_id, []))

        if not queues:
            return

        for queue in queues:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                self._logger.debug("SSE队列已满，跳过推送: user_id=%s", user_id)

    def _format_sse(self, event: str, data: Dict[str, Any]) -> str:
        """格式化SSE消息。

        Args:
            event: 事件名称。
            data: 事件数据。

        Returns:
            SSE格式的字符串。
        """
        payload = json.dumps(data, ensure_ascii=True)
        return f"event: {event}\ndata: {payload}\n\n"
