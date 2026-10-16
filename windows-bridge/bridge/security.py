from pathlib import Path

def is_path_allowed(requested: str, allowed_dirs: list[str]) -> bool:
    try:
        req = Path(requested).resolve()
        for d in allowed_dirs:
            try:
                allowed = Path(d).resolve()
                if str(req).lower().startswith(str(allowed).lower()):
                    return True
                # also check via relative_to for strict
                try:
                    req.relative_to(allowed)
                    return True
                except ValueError:
                    continue
            except:
                continue
        return False
    except:
        return False

def is_app_allowed(app_id: str, allowed_apps: list[dict]) -> bool:
    return any(a.get("id") == app_id for a in allowed_apps)

def get_app_exec(app_id: str, allowed_apps: list[dict]) -> str | None:
    for a in allowed_apps:
        if a.get("id") == app_id:
            return a.get("exec")
    return None
