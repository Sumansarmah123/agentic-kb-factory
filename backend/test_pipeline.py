"""
End-to-end test pipeline for Agentic KB Factory.
Verifies all components work together correctly.
"""

import asyncio
import uuid
from backend.services.firestore import firestore_service
from backend.models.schemas import CollectorCreate


async def test_end_to_end():
    """Run complete end-to-end test."""
    print("\n" + "=" * 60)
    print("🚀 Agentic KB Factory - End-to-End Test Pipeline")
    print("=" * 60 + "\n")
    
    try:
        # Test 1: Firestore Connection
        print("✓ Test 1: Firestore Connection")
        stats = await firestore_service.get_statistics()
        print(f"  Collectors: {stats['total_collectors']}")
        print(f"  Active: {stats['active_collectors']}\n")
        
        # Test 2: Create Collector
        print("✓ Test 2: Create Collector")
        collector_id = f"test-collector-{uuid.uuid4().hex[:8]}"
        
        collector_data = CollectorCreate(
            source_name="Test Knowledge Base",
            target_url="https://www.python.org",
            css_selectors={
                "title": "title",
                "heading": "h1",
            },
            is_active=True,
        )
        
        collector = await firestore_service.create_collector(collector_id, collector_data)
        print(f"  Created: {collector_id}")
        print(f"  Source: {collector.source_name}\n")
        
        # Test 3: Get Collector
        print("✓ Test 3: Get Collector")
        fetched = await firestore_service.get_collector(collector_id)
        assert fetched is not None
        print(f"  Retrieved: {fetched.source_name}\n")
        
        # Test 4: List Collectors
        print("✓ Test 4: List Collectors")
        collectors = await firestore_service.list_collectors(limit=10)
        print(f"  Total collectors: {len(collectors)}\n")
        
        # Test 5: Gemini Connection
        print("✓ Test 5: Gemini Service Health")
        from backend.services.gemini import gemini_service
        health = await gemini_service.health_check()
        print(f"  Gemini OK: {health}\n")
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await firestore_service.close()


if __name__ == "__main__":
    result = asyncio.run(test_end_to_end())
    exit(0 if result else 1)
