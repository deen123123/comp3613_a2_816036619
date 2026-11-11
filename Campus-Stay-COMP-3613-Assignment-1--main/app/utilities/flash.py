from fastapi import Request


def flash(request: Request, message: str, category: str = "info") -> None:
    flashes = list(request.session.get("_flashes", []))
    flashes.append({"message": message, "category": category})
    request.session["_flashes"] = flashes


def pop_flashes(request: Request) -> list:
    return request.session.pop("_flashes", [])
