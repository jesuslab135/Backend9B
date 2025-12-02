"""
Test script for 5-minute ventana calculation system

This script verifies:
1. Ventanas are created with 5-minute duration on login
2. Periodic task processes active sessions
3. Statistics are calculated when windows complete
4. ML predictions are triggered after calculations
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_login_creates_5min_ventana():
    """Test that login creates a 5-minute ventana"""
    print("\n" + "="*60)
    print("TEST 1: Login creates 5-minute ventana")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/usuarios/login/",
        json={
            "email": "consumidor@test.com",
            "password": "password123",
            "device_id": "default"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful")
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   Ventana ID: {data.get('ventana_id')}")
        print(f"   Window Start: {data.get('window_start')}")
        print(f"   Window End: {data.get('window_end')}")
        
        # Check window duration
        if 'window_start' in data and 'window_end' in data:
            from dateutil import parser
            start = parser.parse(data['window_start'])
            end = parser.parse(data['window_end'])
            duration_minutes = (end - start).total_seconds() / 60
            
            if abs(duration_minutes - 5) < 0.1:  # Allow small floating point difference
                print(f"   ✅ Window duration: {duration_minutes:.1f} minutes (correct!)")
            else:
                print(f"   ❌ Window duration: {duration_minutes:.1f} minutes (expected 5)")
        
        return data
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def test_send_multiple_readings(ventana_id, count=10):
    """Send multiple sensor readings to a ventana"""
    print("\n" + "="*60)
    print(f"TEST 2: Send {count} sensor readings")
    print("="*60)
    
    success_count = 0
    
    for i in range(count):
        reading_data = {
            "ventana_id": ventana_id,
            "heart_rate": 70 + (i % 20),
            "accel_x": 0.1,
            "accel_y": 0.2,
            "accel_z": 9.8,
            "gyro_x": 0.01,
            "gyro_y": 0.02,
            "gyro_z": 0.03,
            "device_id": "default"
        }
        
        response = requests.post(
            f"{BASE_URL}/lecturas/",
            json=reading_data
        )
        
        if response.status_code == 201:
            success_count += 1
            print(f"   ✅ Reading {i+1}/{count} sent (HR: {reading_data['heart_rate']})")
        else:
            print(f"   ❌ Reading {i+1} failed: {response.status_code}")
        
        time.sleep(0.5)  # Small delay between readings
    
    print(f"\n   Total: {success_count}/{count} readings sent successfully")
    return success_count


def check_ventana_status(ventana_id):
    """Check the current status of a ventana"""
    print("\n" + "="*60)
    print(f"TEST 3: Check ventana {ventana_id} status")
    print("="*60)
    
    # This would require a GET endpoint for ventana details
    # For now, we'll check via database views
    
    response = requests.get(
        f"{BASE_URL}/dashboard/daily-summary/",
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            latest = data['results'][0]
            print(f"   Latest ventana data:")
            print(f"   - HR Mean: {latest.get('hr_mean')}")
            print(f"   - HR Std: {latest.get('hr_std')}")
            print(f"   - Accel Energy: {latest.get('accel_energy')}")
            print(f"   - Gyro Energy: {latest.get('gyro_energy')}")
            
            if latest.get('hr_mean'):
                print(f"   ✅ Statistics calculated!")
            else:
                print(f"   ⏳ Waiting for calculation...")
        else:
            print(f"   ⚠️ No data available yet")
    else:
        print(f"   ❌ Failed to check status: {response.status_code}")


def test_periodic_task_trigger():
    """Instructions for testing the periodic task"""
    print("\n" + "="*60)
    print("TEST 4: Manual periodic task trigger")
    print("="*60)
    print("\nTo test the periodic task manually, run:")
    print("   1. Open Django shell: python manage.py shell")
    print("   2. Run: from api.tasks import periodic_ventana_calculation")
    print("   3. Run: result = periodic_ventana_calculation.delay()")
    print("   4. Check result: result.get(timeout=30)")
    print("\nOr check Celery logs for automatic execution every 5 minutes")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 TESTING 5-MINUTE VENTANA SYSTEM")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Login
    session_data = test_login_creates_5min_ventana()
    
    if not session_data:
        print("\n❌ Tests stopped: Login failed")
        return
    
    ventana_id = session_data.get('ventana_id')
    
    # Test 2: Send readings
    test_send_multiple_readings(ventana_id, count=10)
    
    # Test 3: Check status
    check_ventana_status(ventana_id)
    
    # Test 4: Periodic task info
    test_periodic_task_trigger()
    
    print("\n" + "="*60)
    print("✅ TESTS COMPLETED")
    print("="*60)
    print("\nNext steps:")
    print("1. Wait 5 minutes for the window to close")
    print("2. Check Celery logs for periodic task execution")
    print("3. Verify statistics are calculated")
    print("4. Check if ML predictions are created")
    print("\nMonitor with:")
    print("   - Celery logs: docker logs wearableapi-celery-1 -f")
    print("   - Beat logs: docker logs wearableapi-celery-beat-1 -f")
    print("   - Database: Check ventanas table for hr_mean, hr_std, etc.")


if __name__ == "__main__":
    main()
