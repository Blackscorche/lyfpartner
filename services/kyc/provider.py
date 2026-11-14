"""KYC Provider interfaces and implementations (Dojah/Prembly/Mock)."""
from abc import ABC, abstractmethod
import random
from typing import Dict, Any

class KYCProvider(ABC):
    @abstractmethod
    async def verify_bvn(self, bvn: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def verify_nin(self, nin: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def check_face_match(self, image_base64: str) -> Dict[str, Any]:
        pass

class MockKYCProvider(KYCProvider):
    async def verify_bvn(self, bvn: str) -> Dict[str, Any]:
        clean_bvn = bvn.replace(" ", "").replace("-", "")
        if len(clean_bvn) != 11 or not clean_bvn.isdigit():
            return {"valid": False, "reason": "BVN must be 11 numeric digits"}
        
        # Mock Nigerian identity response
        return {
            "valid": True,
            "bvn": clean_bvn,
            "first_name": "Amina",
            "last_name": "Ibrahim",
            "date_of_birth": "1994-06-15",
            "gender": "Female",
            "phone_number": "+2348012345678"
        }

    async def verify_nin(self, nin: str) -> Dict[str, Any]:
        clean_nin = nin.replace(" ", "").replace("-", "")
        if len(clean_nin) != 11 or not clean_nin.isdigit():
            return {"valid": False, "reason": "NIN must be 11 numeric digits"}
        return {
            "valid": True,
            "nin": clean_nin,
            "first_name": "Amina",
            "last_name": "Ibrahim",
            "state_of_origin": "Kaduna",
            "lga": "Zaria"
        }

    async def check_face_match(self, image_base64: str) -> Dict[str, Any]:
        hints = [
            "Please hold still, looking directly into the camera.",
            "Move a little closer to the camera.",
            "Make sure your face is well lit and centered."
        ]
        # Realistic face check simulation
        return {
            "matched": True,
            "confidence": 0.96,
            "guidance_audio_hint": random.choice(hints)
        }

def get_kyc_provider() -> KYCProvider:
    return MockKYCProvider()
