#!/usr/bin/env python3
"""
Test script for Service-to-Service Authentication

This script tests the device metadata endpoint with API Key authentication.
Run this from Monitor_Hermes or any service that needs to consume Monitor_Atlas API.

Usage:
    python test_service_auth.py <device_id>
    
Example:
    python test_service_auth.py 1
"""

import os
import sys
import asyncio
import httpx
from typing import Optional, Dict


class MonitorAtlasClient:
    """Client for consuming Monitor Atlas API with service authentication"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("MONITOR_ATLAS_API_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("SERVICE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "SERVICE_API_KEY not found. Please set it as environment variable or pass it to constructor."
            )
    
    @property
    def headers(self) -> Dict[str, str]:
        """Return headers with API Key authentication"""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "MonitorHermes/1.0"
        }
    
    async def get_device_metadata(self, device_id: int) -> Optional[Dict]:
        """
        Retrieve device metadata from Monitor Atlas API.
        
        Args:
            device_id: The ID of the device
            
        Returns:
            Dict with device metadata or None if not found
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        endpoint = f"{self.base_url}/api/devices/{device_id}/metadata/"
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"🔄 Requesting: {endpoint}")
                print(f"🔑 Using API Key: {self.api_key[:8]}...{self.api_key[-4:]}")
                
                response = await client.get(
                    endpoint,
                    headers=self.headers,
                    timeout=10.0
                )
                
                print(f"📊 Status Code: {response.status_code}")
                
                response.raise_for_status()
                
                data = response.json()
                print(f"✅ Success! Retrieved metadata for device: {data.get('name')}")
                return data
                
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP Error: {e.response.status_code}")
                print(f"Response: {e.response.text}")
                
                if e.response.status_code == 401:
                    print("\n💡 Tip: Check that your API key is correct")
                elif e.response.status_code == 403:
                    print("\n💡 Tip: Your API key was accepted but you don't have permission")
                elif e.response.status_code == 404:
                    print(f"\n💡 Tip: Device with ID {device_id} not found")
                
                raise
                
            except httpx.RequestError as e:
                print(f"❌ Connection Error: {e}")
                print("\n💡 Tip: Make sure Monitor Atlas API is running")
                raise


def print_device_metadata(metadata: Dict):
    """Pretty print device metadata"""
    print("\n" + "="*60)
    print("📱 DEVICE METADATA")
    print("="*60)
    
    print(f"\n🔧 Basic Info:")
    print(f"  DevEUI:        {metadata.get('dev_eui')}")
    print(f"  Name:          {metadata.get('name')}")
    print(f"  Description:   {metadata.get('description')}")
    print(f"  Is Active:     {metadata.get('is_active')}")
    print(f"  Is Disabled:   {metadata.get('is_disabled')}")
    
    machine = metadata.get('machine', {})
    print(f"\n🏭 Machine:")
    print(f"  ID:            {machine.get('id')}")
    print(f"  Name:          {machine.get('name')}")
    print(f"  Description:   {machine.get('description')}")
    
    device_type = metadata.get('device_type', {})
    print(f"\n📦 Device Type:")
    print(f"  ID:            {device_type.get('id')}")
    print(f"  Name:          {device_type.get('name')}")
    print(f"  Description:   {device_type.get('description')}")
    
    application = metadata.get('application', {})
    print(f"\n📲 Application:")
    print(f"  ID:            {application.get('id')}")
    print(f"  CS App ID:     {application.get('cs_application_id')}")
    print(f"  Name:          {application.get('name')}")
    
    workspace = metadata.get('workspace', {})
    print(f"\n🏢 Workspace:")
    print(f"  ID:            {workspace.get('id')}")
    print(f"  Name:          {workspace.get('name')}")
    
    measurements = metadata.get('measurements', [])
    print(f"\n📊 Measurements: ({len(measurements)} configured)")
    for i, m in enumerate(measurements, 1):
        print(f"  {i}. Min: {m.get('min')}, Max: {m.get('max')}, "
              f"Threshold: {m.get('threshold')}, Unit: {m.get('unit')}")
    
    activation = metadata.get('activation')
    if activation:
        print(f"\n🔐 Activation:")
        print(f"  ID:            {activation.get('id')}")
        print(f"  Dev Addr:      {activation.get('dev_addr')}")
        print(f"  F Cnt Up:      {activation.get('f_cnt_up')}")
    else:
        print(f"\n🔐 Activation: Not configured")
    
    print(f"\n🔄 Sync Status:   {metadata.get('sync_status')}")
    print(f"⏰ Last Synced:   {metadata.get('last_synced_at')}")
    print(f"👀 Last Seen:     {metadata.get('last_seen_at')}")
    print("\n" + "="*60)


async def test_authentication_scenarios(client: MonitorAtlasClient, device_id: int):
    """Test different authentication scenarios"""
    print("\n" + "="*60)
    print("🧪 TESTING AUTHENTICATION SCENARIOS")
    print("="*60)
    
    # Test 1: Valid API Key
    print("\n📝 Test 1: Valid API Key")
    try:
        metadata = await client.get_device_metadata(device_id)
        print("✅ Test 1 PASSED")
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
    
    # Test 2: Invalid API Key
    print("\n📝 Test 2: Invalid API Key")
    invalid_client = MonitorAtlasClient(
        base_url=client.base_url,
        api_key="invalid-key-should-fail"
    )
    try:
        await invalid_client.get_device_metadata(device_id)
        print("❌ Test 2 FAILED: Should have raised an error")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("✅ Test 2 PASSED: Got 401 as expected")
        else:
            print(f"❌ Test 2 FAILED: Got {e.response.status_code} instead of 401")
    
    # Test 3: Non-existent device
    print("\n📝 Test 3: Non-existent Device")
    try:
        await client.get_device_metadata(999999)
        print("❌ Test 3 FAILED: Should have raised an error")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print("✅ Test 3 PASSED: Got 404 as expected")
        else:
            print(f"❌ Test 3 FAILED: Got {e.response.status_code} instead of 404")


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_service_auth.py <device_id>")
        print("\nExample: python test_service_auth.py 1")
        sys.exit(1)
    
    try:
        device_id = int(sys.argv[1])
    except ValueError:
        print(f"❌ Error: '{sys.argv[1]}' is not a valid device ID")
        sys.exit(1)
    
    # Check for environment variables
    api_key = os.getenv("SERVICE_API_KEY")
    base_url = os.getenv("MONITOR_ATLAS_API_URL", "http://localhost:8000")
    
    if not api_key:
        print("❌ Error: SERVICE_API_KEY environment variable not set")
        print("\n💡 Set it with:")
        print("   export SERVICE_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    print("🚀 Monitor Atlas Service Authentication Test")
    print(f"🌐 API URL: {base_url}")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"📱 Device ID: {device_id}")
    
    try:
        # Initialize client
        client = MonitorAtlasClient(base_url=base_url, api_key=api_key)
        
        # Get device metadata
        metadata = await client.get_device_metadata(device_id)
        
        if metadata:
            print_device_metadata(metadata)
        
        # Run authentication tests
        run_tests = input("\n🧪 Run authentication tests? (y/n): ").lower()
        if run_tests == 'y':
            await test_authentication_scenarios(client, device_id)
        
        print("\n✨ All done!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
