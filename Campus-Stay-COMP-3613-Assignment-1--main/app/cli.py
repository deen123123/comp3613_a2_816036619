"""Project CLI (stdlib argparse).

    python manage.py init     # create tables (drops by default) and seed demo data
    python manage.py run
"""

import argparse
import os

from tabulate import tabulate

from app.config import settings


def cmd_init(args) -> None:
    from sqlmodel import Session

    from app.database import create_db, engine
    from app.seed import seed

    create_db(drop=not args.no_drop)
    print("Database tables ready" + ("" if args.no_drop else " (existing tables dropped)") + ".")
    if args.no_seed:
        return
    with Session(engine) as session:
        summary = seed(session)
    print(f"Seed ok: {summary}")


def cmd_seed(args) -> None:
    from sqlmodel import Session

    from app.database import create_db, engine
    from app.seed import seed

    create_db(drop=False)
    with Session(engine) as session:
        print(f"Seed ok: {seed(session)}")


def cmd_users(args) -> None:
    from sqlmodel import Session

    from app.database import engine
    from app.repositories import user_repo

    with Session(engine) as session:
        rows = [[u.id, u.username, u.email, u.role] for u in user_repo.list_all(session)]
    print(tabulate(rows, headers=["id", "username", "email", "role"]) if rows else "No users yet. Run: python manage.py init")


def cmd_run(args) -> None:
    import uvicorn

    host = args.host or ("0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    port = args.port or settings.port
    reload = not (settings.is_production or args.no_reload)
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


def main() -> None:
    parser = argparse.ArgumentParser(prog="manage.py", description="Campus Stay project CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Create tables (drop first by default) and seed demo data")
    p.add_argument("--no-drop", action="store_true", help="Keep existing tables")
    p.add_argument("--no-seed", action="store_true", help="Skip demo data")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("seed", help="Insert demo data without touching existing rows")
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser("users", help="List users")
    p.set_defaults(func=cmd_users)

    p = sub.add_parser("run", help="Start the web server")
    p.add_argument("--host")
    p.add_argument("--port", type=int)
    p.add_argument("--no-reload", action="store_true")
    p.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)
