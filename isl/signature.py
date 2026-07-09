"""
ISL v1.1 Cryptographic Signature Implementation

This module implements the signature scheme as specified in ISL v1.1
Section 10.1, including key management, signature creation, and verification.
"""

from typing import Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from cryptography.exceptions import InvalidSignature


class SignatureScheme:
    """
    ISL v1.1 signature scheme using Ed25519.
    
    Per CIEMS-ISL-0011 Section 10.1, the signature scheme uses Ed25519
    for cryptographic signatures over the canonical serialization of
    ISL payloads.
    """
    
    ALGORITHM = "Ed25519"
    
    @staticmethod
    def generate_key_pair() -> Tuple[bytes, bytes]:
        """
        Generate a new Ed25519 key pair for CIEMS agent registration.
        
        Returns:
            Tuple of (private_key_bytes, public_key_bytes)
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_bytes = private_key.private_bytes(
            encoding=Encoding.Raw,
            format=PrivateFormat.Raw,
            encryption_algorithm=NoEncryption()
        )
        
        public_bytes = public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw,
        )
        
        return private_bytes, public_bytes
    
    @staticmethod
    def private_key_from_bytes(private_key_bytes: bytes) -> ed25519.Ed25519PrivateKey:
        """Load Ed25519 private key from bytes."""
        return ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    
    @staticmethod
    def public_key_from_bytes(public_key_bytes: bytes) -> ed25519.Ed25519PublicKey:
        """Load Ed25519 public key from bytes."""
        return ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)


def create_signature(canonical_payload: str, private_key_bytes: bytes) -> str:
    """
    Create a cryptographic signature over the canonical payload serialization.
    
    Args:
        canonical_payload: The canonical JSON serialization of the payload
        private_key_bytes: The agent's private key in raw bytes format
        
    Returns:
        Hex-encoded signature string
    """
    private_key = SignatureScheme.private_key_from_bytes(private_key_bytes)
    
    signature = private_key.sign(canonical_payload.encode("utf-8"))
    
    return signature.hex()


def verify_signature(
    canonical_payload: str,
    signature_hex: str,
    public_key_bytes: bytes
) -> bool:
    """
    Verify a cryptographic signature over the canonical payload serialization.
    
    Args:
        canonical_payload: The canonical JSON serialization of the payload
        signature_hex: The hex-encoded signature to verify
        public_key_bytes: The agent's public key in raw bytes format
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        public_key = SignatureScheme.public_key_from_bytes(public_key_bytes)
        signature = bytes.fromhex(signature_hex)
        
        public_key.verify(signature, canonical_payload.encode("utf-8"))
        return True
        
    except (InvalidSignature, ValueError):
        return False


def verify_co_author_signatures(
    canonical_payload: str,
    co_author_signatures: list,
    agent_registry: dict
) -> Tuple[bool, list[str]]:
    """
    Verify all co-author signatures in a composition payload.
    
    Args:
        canonical_payload: The canonical JSON serialization
        co_author_signatures: List of CoAuthorSignature objects
        agent_registry: Registry mapping agent_id to public_key_bytes
        
    Returns:
        Tuple of (all_valid, failed_agent_ids)
    """
    failed_agent_ids = []
    
    for co_sig in co_author_signatures:
        agent_id = co_sig.agent_id
        signature = co_sig.signature
        
        if agent_id not in agent_registry:
            failed_agent_ids.append(agent_id)
            continue
        
        public_key_bytes = agent_registry[agent_id]
        
        if not verify_signature(canonical_payload, signature, public_key_bytes):
            failed_agent_ids.append(agent_id)
    
    return len(failed_agent_ids) == 0, failed_agent_ids
