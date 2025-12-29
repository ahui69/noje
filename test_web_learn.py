#!/usr/bin/env python3
import sys
import asyncio
sys.path.insert(0, "/workspace/mrd")

async def test_web_learn():
    from core.research import _web_learn_async
    from core.config import SERPAPI_KEY, FIRECRAWL_API_KEY
    
    print(f"SERPAPI_KEY: {'SET' if SERPAPI_KEY else 'NOT SET'}")
    print(f"FIRECRAWL_API_KEY: {'SET' if FIRECRAWL_API_KEY else 'NOT SET'}")
    
    print("\n=== TESTING _web_learn_async ===")
    result = await _web_learn_async("najnowsze wiadomości z Polski", mode="fast")
    
    print(f"\nResult:")
    print(f"  Query: {result.query}")
    print(f"  Count: {result.count}")
    print(f"  Trust: {result.trust_avg}")
    print(f"  Backend: {result.backend}")
    print(f"  Draft: {result.draft[:200] if result.draft else 'BRAK'}")
    print(f"  Citations: {len(result.citations)}")
    
asyncio.run(test_web_learn())
