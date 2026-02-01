"""
Load Test Script - Test concurrent users.

Simulates multiple users asking questions simultaneously.
"""
import asyncio
import aiohttp
import time
from typing import List, Dict
import json
from datetime import datetime

API_URL = "http://localhost:8000/api/chat/"

# Test questions (mix of popular and unique)
POPULAR_QUESTIONS = [
    "Lisans programları kaç yıldır?",
    "Yaz okulu kaç hafta sürer?",
    "Üst sınıftan ders alabilir miyim?",
]

UNIQUE_QUESTIONS = [
    "Mezuniyet için hangi belgeler gerekir?",
    "Staj süresi kaç hafta?",
    "Ders kayıt tarihleri ne zaman?",
    "Not ortalaması nasıl hesaplanır?",
    "Akademik takvim nerede bulunur?",
    "Disiplin cezaları nelerdir?",
    "Ders silme işlemi nasıl yapılır?",
]


async def send_question(session: aiohttp.ClientSession, question: str, user_id: int) -> Dict:
    """
    Send a single question to the API.
    
    Args:
        session: aiohttp session
        question: Question to ask
        user_id: User identifier
    
    Returns:
        Result dictionary with timing and response info
    """
    start_time = time.time()
    
    try:
        async with session.post(
            API_URL,
            json={"question": question, "include_sources": True},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            elapsed = time.time() - start_time
            
            if response.status == 200:
                data = await response.json()
                
                return {
                    "user_id": user_id,
                    "question": question,
                    "status": "success",
                    "response_time": elapsed,
                    "tokens": data.get("metadata", {}).get("tokens", 0),
                    "cost": data.get("metadata", {}).get("cost", 0),
                    "cached": data.get("metadata", {}).get("cached", False),
                    "answer_preview": data.get("answer", "")[:100] + "..."
                }
            else:
                return {
                    "user_id": user_id,
                    "question": question,
                    "status": "error",
                    "response_time": elapsed,
                    "error": f"HTTP {response.status}"
                }
    
    except asyncio.TimeoutError:
        return {
            "user_id": user_id,
            "question": question,
            "status": "timeout",
            "response_time": 30.0,
            "error": "Request timeout (>30s)"
        }
    
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "user_id": user_id,
            "question": question,
            "status": "error",
            "response_time": elapsed,
            "error": str(e)
        }


async def run_load_test(num_users: int, question_distribution: str = "mixed"):
    """
    Run load test with concurrent users.
    
    Args:
        num_users: Number of concurrent users to simulate
        question_distribution: 'popular' (80% same questions), 'mixed', or 'unique'
    """
    print(f"\n{'='*60}")
    print(f"🚀 LOAD TEST: {num_users} Concurrent Users")
    print(f"📊 Distribution: {question_distribution}")
    print(f"{'='*60}\n")
    
    # Generate questions based on distribution
    questions = []
    
    if question_distribution == "popular":
        # 80% popular, 20% unique (realistic scenario)
        for i in range(num_users):
            if i < num_users * 0.8:
                questions.append(POPULAR_QUESTIONS[i % len(POPULAR_QUESTIONS)])
            else:
                questions.append(UNIQUE_QUESTIONS[i % len(UNIQUE_QUESTIONS)])
    
    elif question_distribution == "unique":
        # All unique questions (worst case)
        questions = [UNIQUE_QUESTIONS[i % len(UNIQUE_QUESTIONS)] for i in range(num_users)]
    
    else:  # mixed
        # 50% popular, 50% unique
        for i in range(num_users):
            if i % 2 == 0:
                questions.append(POPULAR_QUESTIONS[i % len(POPULAR_QUESTIONS)])
            else:
                questions.append(UNIQUE_QUESTIONS[i % len(UNIQUE_QUESTIONS)])
    
    # Create tasks
    async with aiohttp.ClientSession() as session:
        print(f"⏱️  Starting test at {datetime.now().strftime('%H:%M:%S')}")
        start_time = time.time()
        
        tasks = [
            send_question(session, questions[i], user_id=i+1)
            for i in range(num_users)
        ]
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks)
        
        total_elapsed = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]
    timeouts = [r for r in results if r["status"] == "timeout"]
    cached = [r for r in successful if r.get("cached", False)]
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTS")
    print(f"{'='*60}\n")
    
    print(f"✅ Successful: {len(successful)}/{num_users} ({len(successful)/num_users*100:.1f}%)")
    print(f"❌ Errors: {len(errors)}/{num_users} ({len(errors)/num_users*100:.1f}%)")
    print(f"⏱️  Timeouts: {len(timeouts)}/{num_users} ({len(timeouts)/num_users*100:.1f}%)")
    
    if successful:
        cache_hit_rate = len(cached)/len(successful)*100
        print(f"🎯 Cache Hits: {len(cached)}/{len(successful)} ({cache_hit_rate:.1f}%)")
    else:
        print(f"🎯 Cache Hits: 0/0 (0.0%)")
    
    if successful:
        response_times = [r["response_time"] for r in successful]
        tokens = [r["tokens"] for r in successful]
        costs = [r["cost"] for r in successful]
        
        print(f"\n⏱️  Response Times:")
        print(f"   Min: {min(response_times):.2f}s")
        print(f"   Max: {max(response_times):.2f}s")
        print(f"   Avg: {sum(response_times)/len(response_times):.2f}s")
        print(f"   Median: {sorted(response_times)[len(response_times)//2]:.2f}s")
        
        print(f"\n💰 Costs:")
        print(f"   Total: ${sum(costs):.4f}")
        print(f"   Average per request: ${sum(costs)/len(costs):.4f}")
        
        print(f"\n🔢 Tokens:")
        print(f"   Total: {sum(tokens):,}")
        print(f"   Average per request: {sum(tokens)/len(tokens):.0f}")
        
        print(f"\n🚀 Throughput:")
        print(f"   Total time: {total_elapsed:.2f}s")
        print(f"   Requests/second: {num_users/total_elapsed:.2f}")
    
    if errors:
        print(f"\n❌ Errors:")
        for err in errors[:5]:  # Show first 5 errors
            print(f"   User {err['user_id']}: {err['error']}")
        if len(errors) > 5:
            print(f"   ... and {len(errors)-5} more errors")
    
    print(f"\n{'='*60}\n")
    
    return results


async def main():
    """Run multiple load test scenarios."""
    
    print("\n" + "="*60)
    print("🧪 SUBU CHATBOT LOAD TEST")
    print("="*60)
    
    # Scenario 1: 10 users (warm-up)
    print("\n📌 Scenario 1: Light Load (10 users)")
    await run_load_test(10, "mixed")
    await asyncio.sleep(2)
    
    # Scenario 2: 50 users with popular questions (cache test)
    print("\n📌 Scenario 2: Medium Load with Cache (50 users, 80% popular)")
    await run_load_test(50, "popular")
    await asyncio.sleep(2)
    
    # Scenario 3: 100 users all unique (worst case)
    print("\n📌 Scenario 3: High Load, No Cache (100 users, all unique)")
    print("⚠️  WARNING: This may hit rate limits!")
    
    response = input("\nContinue with 100 concurrent users? (y/n): ")
    if response.lower() == 'y':
        await run_load_test(100, "unique")
    else:
        print("Skipped.")
    
    print("\n✅ Load test complete!")


if __name__ == "__main__":
    asyncio.run(main())
