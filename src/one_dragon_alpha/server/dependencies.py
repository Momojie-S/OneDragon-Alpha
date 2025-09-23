"""Dependency injection utilities for OneDragon Alpha server."""

from fastapi import Depends, HTTPException
from typing import Annotated
from one_dragon_alpha.server.context import OneDragonAlphaContext


def get_context() -> OneDragonAlphaContext:
    """Get the global context instance for dependency injection."""
    context = OneDragonAlphaContext.get_instance()
    if context is None:
        raise HTTPException(
            status_code=500,
            detail="Context not initialized. Please ensure the server is properly started."
        )
    return context


ContextDep = Annotated[OneDragonAlphaContext, Depends(get_context)]