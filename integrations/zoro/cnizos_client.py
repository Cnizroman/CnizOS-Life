"""
CnizOS Client для голосового помощника Зоро
Сохрани этот файл рядом с main.py Зоро: from cnizos_client import CnizOSClient

Все методы соответствуют реальному API /api/v1/zoro/* Backend.
Не дублирует бизнес-логику — только тонкий HTTP-клиент.
"""
import httpx
import json
from typing import Optional, List, Dict, Any

class CnizOSError(Exception): pass
class AuthError(CnizOSError): pass
class NotFound(CnizOSError): pass
class BridgeOffline(CnizOSError): pass
class ServerUnavailable(CnizOSError): pass

class CnizOSClient:
    def __init__(self, base_url: str, token: str, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _url(self, path: str) -> str:
        if path.startswith("/"):
            return f"{self.base_url}/api/v1{path}"
        return f"{self.base_url}/api/v1/{path}"

    def _handle(self, resp: httpx.Response):
        if resp.status_code == 401:
            raise AuthError(f"Auth failed: {resp.text}")
        if resp.status_code == 404:
            raise NotFound(resp.text)
        if resp.status_code == 502:
            raise BridgeOffline(resp.text)
        if resp.status_code >= 500:
            raise ServerUnavailable(resp.text)
        resp.raise_for_status()
        try:
            return resp.json()
        except:
            return resp.text

    # Tasks
    def get_tasks(self, view: Optional[str] = None) -> List[Dict]:
        params = {}
        if view:
            params["view"] = view
        try:
            r = httpx.get(self._url("/zoro/tasks"), headers=self.headers, params=params, timeout=self.timeout)
            return self._handle(r).get("data", [])
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def create_task(self, title: str, description: Optional[str] = None, due_date: Optional[str] = None, priority: str = "medium") -> Dict:
        payload = {"title": title, "priority": priority}
        if description: payload["description"] = description
        if due_date: payload["due_date"] = due_date
        try:
            r = httpx.post(self._url("/zoro/tasks"), headers=self.headers, json=payload, timeout=self.timeout)
            return self._handle(r)
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def update_task(self, task_id: str, **kwargs) -> Dict:
        try:
            r = httpx.patch(self._url(f"/zoro/tasks/{task_id}"), headers=self.headers, json=kwargs, timeout=self.timeout)
            return self._handle(r)
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def get_task(self, task_id: str) -> Dict:
        # fallback to direct tasks endpoint
        try:
            r = httpx.get(self._url(f"/tasks/{task_id}"), headers=self.headers, timeout=self.timeout)
            return self._handle(r)
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    # Notes
    def search_notes(self, q: str, limit: int = 5) -> List[Dict]:
        try:
            r = httpx.get(self._url("/zoro/notes/search"), headers=self.headers, params={"q": q, "limit": limit}, timeout=self.timeout)
            return self._handle(r).get("data", [])
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def create_note(self, title: str, body: Optional[str] = None, type: str = "note", project_ids: Optional[List[str]] = None) -> Dict:
        payload = {"title": title, "body": body or title, "type": type}
        if project_ids: payload["project_ids"] = project_ids
        try:
            r = httpx.post(self._url("/zoro/notes"), headers=self.headers, json=payload, timeout=self.timeout)
            return self._handle(r)
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def get_note(self, note_id: str) -> Dict:
        try:
            r = httpx.get(self._url(f"/notes/{note_id}"), headers=self.headers, timeout=self.timeout)
            return self._handle(r)
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    # Projects
    def list_projects(self, q: Optional[str] = None) -> List[Dict]:
        params = {}
        if q: params["q"] = q
        try:
            r = httpx.get(self._url("/zoro/projects"), headers=self.headers, params=params, timeout=self.timeout)
            return self._handle(r).get("data", [])
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def get_project(self, project_id: str) -> Dict:
        try:
            r = httpx.get(self._url(f"/zoro/projects/{project_id}"), headers=self.headers, timeout=self.timeout)
            return self._handle(r)
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    # Bridge
    def get_bridge_status(self) -> Dict:
        try:
            r = httpx.get(self._url("/zoro/bridge/status"), headers=self.headers, timeout=self.timeout)
            return self._handle(r)
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def execute_action(self, action: str, params: Dict[str, Any] = {}, confirm: bool = False) -> Dict:
        # confirm flag is for future dangerous actions
        payload = {"action": action, "params": params}
        try:
            r = httpx.post(self._url("/zoro/actions/execute"), headers=self.headers, json=payload, timeout=self.timeout)
            return self._handle(r)
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def get_history(self, limit: int = 20) -> List[Dict]:
        try:
            r = httpx.get(self._url("/zoro/history"), headers=self.headers, params={"limit": limit}, timeout=self.timeout)
            return self._handle(r).get("data", [])
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))

    def search(self, q: str) -> List[Dict]:
        try:
            r = httpx.get(self._url("/search"), headers=self.headers, params={"q": q}, timeout=self.timeout)
            return self._handle(r).get("results", [])
        except httpx.ConnectError as e:
            raise ServerUnavailable(str(e))


# Example usage for Zoro intents:
# client = CnizOSClient(base_url="https://cnizos.example.com", token="your_zoro_token")
#
# # handle_cnizos_note
# def handle_cnizos_note(text):
#     try:
#         note = client.create_note(title=text)
#         speak(f"Сохранил заметку {note['title']}")
#     except ServerUnavailable:
#         speak("CnizOS недоступен, записал локально")
#         # save to pending file
