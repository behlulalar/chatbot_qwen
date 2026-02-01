"""
Test FastAPI server.

This script tests API endpoints using requests library.

Usage:
    # Terminal 1: Start server
    python app/main.py
    
    # Terminal 2: Run tests
    python test_api.py
"""
import requests
import json
import time


BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("=" * 80)
    print("TEST: Health Check")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/health")
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_chat():
    """Test chat endpoint."""
    print("\n" + "=" * 80)
    print("TEST: Chat Endpoint")
    print("=" * 80)
    
    # Test question
    payload = {
        "question": "Akademik personele ödül nasıl verilir?",
        "include_sources": True
    }
    
    print(f"\n❓ Soru: {payload['question']}")
    print("⏳ Cevap bekleniyor...")
    
    start = time.time()
    response = requests.post(f"{BASE_URL}/api/chat/", json=payload)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ Başarılı! ({elapsed:.2f}s)")
        print(f"\n🤖 Cevap:")
        print(data['answer'])
        
        print(f"\n📚 Kaynaklar: {len(data['sources'])}")
        for i, source in enumerate(data['sources'][:3], 1):
            print(f"  {i}. {source['title'][:50]}... (Madde {source['article_number']})")
        
        print(f"\n📊 Metadata:")
        print(f"  Tokens: {data['metadata']['tokens']}")
        print(f"  Cost: ${data['metadata']['cost']:.4f}")
        print(f"  Model: {data['metadata']['model']}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200


def test_documents():
    """Test documents endpoint."""
    print("\n" + "=" * 80)
    print("TEST: Documents List")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/api/documents/?limit=5")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ Success!")
        print(f"\nTotal documents: {data['total']}")
        print(f"\nFirst 5 documents:")
        
        for i, doc in enumerate(data['documents'], 1):
            print(f"\n  {i}. {doc['title'][:50]}...")
            print(f"     Status: {doc['status']}")
            print(f"     Pages: {doc['page_count']}")
            if doc['article_count']:
                print(f"     Articles: {doc['article_count']}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200


def test_interactive():
    """Interactive chat test."""
    print("\n" + "=" * 80)
    print("TEST: Interactive Chat (via API)")
    print("=" * 80)
    print("\nÇıkmak için 'exit' yazın\n")
    
    while True:
        question = input("❓ Soru: ").strip()
        
        if not question or question.lower() == 'exit':
            print("\n👋 Test sonlandırıldı")
            break
        
        print("⏳ Cevap bekleniyor...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat/",
                json={"question": question, "include_sources": True},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n🤖 Cevap:\n{data['answer']}")
                
                if data['sources']:
                    print(f"\n📚 Kaynak: {data['sources'][0]['title']}")
                
                print(f"💰 ${data['metadata']['cost']:.4f}\n")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}\n")
        
        except Exception as e:
            print(f"❌ Hata: {e}\n")


def main():
    """Main test runner."""
    print("\n" + "=" * 80)
    print("FASTAPI SERVER TEST")
    print("=" * 80)
    print(f"\nBase URL: {BASE_URL}")
    print("\n⚠️ Make sure server is running!")
    print("   Start with: python app/main.py")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        print(f"\n✅ Server is running!")
    except:
        print(f"\n❌ Server not responding!")
        print("\n   Start server in another terminal:")
        print("   cd backend")
        print("   python app/main.py")
        print("\n   Then run this test again.")
        return
    
    print("\nChoose test:")
    print("1. Health Check")
    print("2. Chat Endpoint")
    print("3. Documents List")
    print("4. Interactive Chat")
    print("5. All Tests")
    print("0. Exit")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        test_health()
    elif choice == "2":
        test_chat()
    elif choice == "3":
        test_documents()
    elif choice == "4":
        test_interactive()
    elif choice == "5":
        test_health()
        test_chat()
        test_documents()
    elif choice == "0":
        print("Exiting...")
        return
    else:
        print("Invalid choice")
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
