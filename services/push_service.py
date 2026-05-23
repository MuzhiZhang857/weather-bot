import os
import logging
import json
import time
import threading
import uuid
import ssl
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
import websocket

load_dotenv()

logger = logging.getLogger(__name__)


class ChatType(Enum):
    SINGLE = 1
    GROUP = 2


@dataclass
class PushMessage:
    chat_id: str
    chat_type: ChatType
    content: str
    msgtype: str = "markdown"  # 恢复为 markdown 格式，与旧版一致


@dataclass
class PushConfig:
    bot_id: str
    secret: str
    ws_url: str = "wss://openws.work.weixin.qq.com"
    heartbeat_interval: int = 30
    max_retry_attempts: int = 3
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 30.0
    connect_timeout: int = 10


class PushService:
    def __init__(self, config: Optional[PushConfig] = None):
        self.config = config or self._load_config_from_env()
        self.ws: Optional[websocket.WebSocketApp] = None
        self._connected: bool = False
        self._subscribed: bool = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_stop_event: threading.Event = threading.Event()
        self._subscribe_timeout_timer: Optional[threading.Timer] = None
        self._message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._event_callback: Optional[Callable[[Dict[str, Any]], None]] = None

        logger.info("PushService 初始化完成")

    def _load_config_from_env(self) -> PushConfig:
        return PushConfig(
            bot_id=os.getenv("BOT_ID", ""),
            secret=os.getenv("SECRET", ""),
            ws_url=os.getenv("WS_URL", "wss://openws.work.weixin.qq.com"),
            heartbeat_interval=int(os.getenv("HEARTBEAT_INTERVAL", "30")),
            max_retry_attempts=int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
            initial_retry_delay=float(os.getenv("INITIAL_RETRY_DELAY", "1.0")),
            max_retry_delay=float(os.getenv("MAX_RETRY_DELAY", "30.0")),
            connect_timeout=int(os.getenv("CONNECT_TIMEOUT", "10")),
        )

    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._message_callback = callback

    def set_event_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._event_callback = callback

    def _generate_req_id(self) -> str:
        return str(uuid.uuid4()).replace("-", "")

    def _calculate_retry_delay(self, attempt: int) -> float:
        delay = self.config.initial_retry_delay * (2 ** (attempt - 1))
        return min(delay, self.config.max_retry_delay)

    def connect_websocket(self) -> bool:
        attempt = 0
        while attempt < self.config.max_retry_attempts:
            attempt += 1
            logger.info(f"尝试建立 WebSocket 连接 (第 {attempt}/{self.config.max_retry_attempts} 次)")

            try:
                self.ws = websocket.WebSocketApp(
                    self.config.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )

                ws_thread = threading.Thread(
                    target=self._run_websocket,
                    daemon=True,
                )
                ws_thread.start()

                start_time = time.time()
                while time.time() - start_time < self.config.connect_timeout:
                    if self._connected and self._subscribed:
                        logger.info("WebSocket 连接成功建立且已订阅")
                        return True
                    time.sleep(0.1)

                logger.warning(f"WebSocket 连接超时 (第 {attempt} 次)")
                self.disconnect()

            except Exception as e:
                logger.error(f"WebSocket 连接失败 (第 {attempt} 次): {str(e)}")

            if attempt < self.config.max_retry_attempts:
                delay = self._calculate_retry_delay(attempt)
                logger.info(f"{delay} 秒后重试...")
                time.sleep(delay)

        logger.error(f"达到最大重试次数 ({self.config.max_retry_attempts})，连接失败")
        return False

    def _run_websocket(self) -> None:
        try:
            self.ws.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE},
                ping_interval=0,
                ping_timeout=99999,
                suppress_origin=True,
            )
        except Exception as e:
            logger.error(f"WebSocket 运行时错误: {str(e)}")

    def subscribe_bot(self) -> bool:
        if not self._connected or not self.ws:
            logger.error("WebSocket 未连接，无法发送订阅请求")
            return False

        req_id = self._generate_req_id()
        subscribe_msg = {
            "cmd": "aibot_subscribe",
            "headers": {
                "req_id": req_id,
                "timestamp": int(time.time())
            },
            "body": {
                "bot_id": self.config.bot_id,
                "secret": self.config.secret
            }
        }

        def on_subscribe_timeout():
            logger.warning("订阅超时，强制断开连接")
            self.disconnect()

        self._subscribe_timeout_timer = threading.Timer(30, on_subscribe_timeout)
        self._subscribe_timeout_timer.start()

        try:
            self.ws.send(json.dumps(subscribe_msg))
            logger.info(f"发送订阅请求: req_id={req_id}")
            return True
        except Exception as e:
            logger.error(f"发送订阅请求失败: {str(e)}")
            if self._subscribe_timeout_timer:
                self._subscribe_timeout_timer.cancel()
                self._subscribe_timeout_timer = None
            return False

    def send_message(self, message: PushMessage) -> bool:
        # 检查连接状态和订阅状态
        if not self._connected:
            logger.error("WebSocket 未连接，无法发送消息")
            return False
        if not self._subscribed:
            logger.error("WebSocket 未订阅，无法发送消息")
            return False
        if not self.ws or not self.ws.sock or not self.ws.sock.connected:
            logger.error("WebSocket socket 未连接，无法发送消息")
            return False

        req_id = self._generate_req_id()
        
        # 使用与旧版一致的消息格式
        ws_message = {
            "cmd": "aibot_send_msg",
            "headers": {
                "req_id": req_id
            },
            "body": {
                "chatid": message.chat_id,
                "chat_type": message.chat_type.value,
                "msgtype": "markdown",  # 强制使用 markdown 格式
                "markdown": {
                    "content": message.content
                }
            }
        }

        # 打印调试日志
        logger.info(f"准备发送消息: chat_id={message.chat_id}, chat_type={message.chat_type.value}")
        logger.info(f"消息内容预览: {message.content[:50]}...")

        attempt = 0
        while attempt < self.config.max_retry_attempts:
            attempt += 1
            try:
                self.ws.send(json.dumps(ws_message))
                logger.info(f"发送消息成功: req_id={req_id}")
                return True
            except Exception as e:
                logger.error(f"发送消息失败 (第 {attempt} 次): {str(e)}")
                if attempt < self.config.max_retry_attempts:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"{delay} 秒后重试...")
                    time.sleep(delay)

        logger.error(f"消息发送达到最大重试次数 ({self.config.max_retry_attempts})，放弃发送")
        return False

    def disconnect(self) -> None:
        logger.info("开始断开 WebSocket 连接")

        self._heartbeat_stop_event.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5)

        if self._subscribe_timeout_timer:
            self._subscribe_timeout_timer.cancel()
            self._subscribe_timeout_timer = None

        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.close()

        self._connected = False
        self._subscribed = False
        self.ws = None

        logger.info("WebSocket 连接已断开")

    def _start_heartbeat(self) -> None:
        self._heartbeat_stop_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
        )
        self._heartbeat_thread.start()
        logger.info("心跳保活已启动")

    def _heartbeat_loop(self) -> None:
        while not self._heartbeat_stop_event.is_set():
            try:
                if self.ws and self.ws.sock and self.ws.sock.connected:
                    req_id = self._generate_req_id()
                    heartbeat = {
                        "cmd": "ping",
                        "headers": {
                            "req_id": req_id
                        }
                    }
                    self.ws.send(json.dumps(heartbeat))
                    logger.debug(f"发送心跳: req_id={req_id}")
            except Exception as e:
                logger.error(f"心跳发送失败: {str(e)}")

            if self._heartbeat_stop_event.wait(self.config.heartbeat_interval):
                break

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        logger.info("WebSocket 连接已打开")
        self._connected = True
        self._start_heartbeat()
        self.subscribe_bot()

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        try:
            data = json.loads(message)
            req_id = data.get('headers', {}).get('req_id', 'N/A')

            if data.get('errcode') == 0:
                logger.debug(f"收到成功响应: req_id={req_id}")
                if self._subscribe_timeout_timer:
                    self._subscribe_timeout_timer.cancel()
                    self._subscribe_timeout_timer = None
                    self._subscribed = True
                    logger.info("订阅成功")
            elif data.get('errcode') != 0:
                logger.error(f"收到错误响应: req_id={req_id}, errcode={data.get('errcode')}, errmsg={data.get('errmsg')}")
                if data.get('errcode') in [40001, 40002, 40003]:
                    logger.error("凭证错误，请检查 Bot ID 和 Secret")

            cmd = data.get('cmd', '')
            if cmd == 'aibot_msg_callback':
                body = data.get('body', {})
                if self._message_callback:
                    self._message_callback(body)
            elif cmd == 'aibot_event_callback':
                body = data.get('body', {})
                if self._event_callback:
                    self._event_callback(body)
            elif cmd == 'pong':
                logger.debug(f"收到 Pong 响应: req_id={req_id}")

        except json.JSONDecodeError:
            logger.error(f"收到非 JSON 消息: {message[:200]}...")
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}")

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        logger.error(f"WebSocket 错误: {str(error)}")

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code: Optional[int], close_msg: Optional[str]) -> None:
        logger.info(f"WebSocket 连接已关闭: status_code={close_status_code}, message={close_msg}")
        self._connected = False
        self._subscribed = False

        self._heartbeat_stop_event.set()
        if self._subscribe_timeout_timer:
            self._subscribe_timeout_timer.cancel()
            self._subscribe_timeout_timer = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_subscribed(self) -> bool:
        return self._subscribed
