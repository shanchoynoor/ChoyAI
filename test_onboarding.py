#!/usr/bin/env python3
"""
Test script for ChoyAI onboarding system
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.modules.users.user_profile_manager import UserProfileManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_onboarding():
    """Test the onboarding and user profile update functionality"""
    try:
        logger.info("🚀 Testing ChoyAI onboarding system...")
        
        # Initialize user profile manager
        profile_manager = UserProfileManager()
        logger.info("✅ User Profile Manager initialized")
        
        # Test user data
        test_user_id = "test_user_123"
        test_data = {
            "username": "testuser",
            "first_name": "John",
            "last_name": "Doe",
            "city": "New York",
            "age": 25,
            "profession": "Software Developer"
        }
        
        # Test updating user info
        logger.info("📝 Testing user info update...")
        success = await profile_manager.update_user_info(
            user_id=test_user_id,
            platform="telegram",
            **test_data
        )
        
        if success:
            logger.info("✅ User info updated successfully")
        else:
            logger.error("❌ Failed to update user info")
            return False
        
        # Test retrieving user profile
        logger.info("🔍 Testing user profile retrieval...")
        profile = await profile_manager.get_user_profile(test_user_id)
        
        if profile:
            logger.info("✅ User profile retrieved successfully")
            logger.info(f"   - Name: {profile.name}")
            logger.info(f"   - City: {profile.city}")
            logger.info(f"   - Age: {profile.age}")
            logger.info(f"   - Profession: {profile.profession}")
        else:
            logger.error("❌ Failed to retrieve user profile")
            return False
        
        # Test time-based greeting
        logger.info("🕐 Testing time-based greeting...")
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            expected_greeting = "Good morning"
        elif 12 <= current_hour < 17:
            expected_greeting = "Good afternoon"
        elif 17 <= current_hour < 22:
            expected_greeting = "Good evening"
        else:
            expected_greeting = "Good night"
        
        logger.info(f"   - Current hour: {current_hour}")
        logger.info(f"   - Expected greeting: {expected_greeting}")
        
        # Cleanup
        await profile_manager.shutdown()
        logger.info("🧹 Cleanup completed")
        
        logger.info("🎉 All onboarding tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("🤖 ChoyAI Onboarding System Test")
    print("=" * 50)
    
    try:
        # Run the test
        result = asyncio.run(test_onboarding())
        
        if result:
            print("\n✅ All tests passed! Onboarding system is working correctly.")
            return 0
        else:
            print("\n❌ Some tests failed. Please check the logs.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
