"""
Clientes HTTP para comunicación con servicios externos.
"""

from app.clients.atlas import AtlasClient, atlas_client

__all__ = ["AtlasClient", "atlas_client"]
