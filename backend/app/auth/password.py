# password.py
# Password hashing and verification utilities

from passlib.context import CryptContext
from typing import Optional


class PasswordManager:
    """Handles password hashing and verification using bcrypt"""
    
    def __init__(self):
        # Initialize password context with bcrypt
        self._pwd_context = CryptContext(
            schemes=["bcrypt"], 
            deprecated="auto",
            bcrypt__rounds=12  # Strong hashing rounds
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password using bcrypt
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
        """
        return self._pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        if not hashed_password:
            return False
        return self._pwd_context.verify(plain_password, hashed_password)
    
    def needs_update(self, hashed_password: str) -> bool:
        """
        Check if a hashed password needs to be rehashed
        
        Args:
            hashed_password: Hashed password to check
            
        Returns:
            True if password needs rehashing, False otherwise
        """
        return self._pwd_context.needs_update(hashed_password)


# Global password manager instance
password_manager = PasswordManager()