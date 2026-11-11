"""Exceptions shared by services, dependencies and the app's handlers."""


class ServiceError(Exception):
    """A business rule was broken. Routes catch this and flash the message."""


class NotFoundError(Exception):
    """The record does not exist (or the viewer may not know it exists)."""


class ForbiddenError(Exception):
    """The signed-in user's role may not do this."""


class LoginRequired(Exception):
    """The visitor must sign in first."""

    def __init__(self, next_url: str = "/"):
        super().__init__(next_url)
        self.next_url = next_url
