"""
Test script for the complete chatbot.

This tests the full RAG + LLM pipeline.

Usage:
    python test_chatbot.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.llm import ResponseGenerator
from app.rag import VectorStoreManager
from app.llm import OpenAIHandler
from app.config import settings


def test_single_question():
    """Test 1: Single question."""
    print("=" * 80)
    print("TEST 1: Single Question")
    print("=" * 80)
    
    # Check API key
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("\n⚠️ OpenAI API key not set!")
        print("   Please set OPENAI_API_KEY in .env file")
        return
    
    # Initialize generator
    print("\n🤖 Initializing chatbot...")
    generator = ResponseGenerator()
    
    # Test question
    question = "Akademik personele ödül nasıl verilir?"
    
    print(f"\n❓ Soru: {question}")
    print("\n⏳ Cevap oluşturuluyor...")
    
    # Generate response
    response = generator.generate_response(question)
    
    # Display response
    print("\n" + "=" * 80)
    print("🤖 CEVAP:")
    print("=" * 80)
    print(response['answer'])
    
    # Display sources
    if response['sources']:
        print("\n" + "=" * 80)
        print("📚 KAYNAKLAR:")
        print("=" * 80)
        for i, source in enumerate(response['sources'], 1):
            print(f"\n{i}. {source['title']}")
            print(f"   Madde: {source['article_number']}")
            print(f"   Uygunluk: {source['relevance_score']:.2%}")
            print(f"   Önizleme: {source['preview'][:150]}...")
    
    # Display metadata
    print("\n" + "=" * 80)
    print("📊 METAVERİ:")
    print("=" * 80)
    print(f"   Model: {response['metadata']['model']}")
    print(f"   Retrieved docs: {response['metadata']['retrieved_docs']}")
    print(f"   Tokens: {response['metadata']['tokens']}")
    print(f"   Cost: ${response['metadata']['cost']:.4f}")
    print(f"   Response time: {response['metadata']['response_time']:.2f}s")


def test_multiple_questions():
    """Test 2: Multiple questions."""
    print("\n" + "=" * 80)
    print("TEST 2: Multiple Questions")
    print("=" * 80)
    
    # Check API key
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("\n⚠️ OpenAI API key not set!")
        return
    
    # Initialize generator
    print("\n🤖 Initializing chatbot...")
    generator = ResponseGenerator()
    
    # Test questions
    questions = [
        "Lisansüstü öğrencilerin azami süreleri nedir?",
        "Bilimsel araştırma projesi başvurusu nasıl yapılır?",
        "Staj süresi ne kadar olmalıdır?"
    ]
    
    total_cost = 0
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'─' * 80}")
        print(f"Soru {i}: {question}")
        print(f"{'─' * 80}")
        
        response = generator.generate_response(question)
        
        print(f"\n🤖 Cevap:")
        print(response['answer'][:300] + "..." if len(response['answer']) > 300 else response['answer'])
        
        print(f"\n📚 Kaynaklar: {len(response['sources'])} doküman")
        if response['sources']:
            print(f"   1. {response['sources'][0]['title']} - Madde {response['sources'][0]['article_number']}")
        
        print(f"💰 Maliyet: ${response['metadata']['cost']:.4f}")
        total_cost += response['metadata']['cost']
    
    print(f"\n{'=' * 80}")
    print(f"💰 TOPLAM MALİYET: ${total_cost:.4f}")
    print(f"{'=' * 80}")


def interactive_mode():
    """Test 3: Interactive chat mode."""
    print("\n" + "=" * 80)
    print("TEST 3: Interactive Chat Mode")
    print("=" * 80)
    
    # Check API key
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("\n⚠️ OpenAI API key not set!")
        return
    
    print("\n🤖 Mevzuat Chatbot başlatılıyor...")
    print("   Çıkmak için 'exit' yazın")
    print("   Yeni sohbet için 'new' yazın\n")
    
    # Initialize generator
    generator = ResponseGenerator()
    conversation_history = []
    total_cost = 0
    
    while True:
        # Get question
        question = input("❓ Soru: ").strip()
        
        if not question:
            continue
        
        if question.lower() == 'exit':
            print(f"\n👋 Görüşmek üzere! Toplam maliyet: ${total_cost:.4f}")
            break
        
        if question.lower() == 'new':
            conversation_history = []
            print("\n🔄 Yeni sohbet başlatıldı\n")
            continue
        
        # Generate response
        print("\n⏳ Düşünüyorum...")
        
        try:
            response = generator.generate_response(
                question,
                conversation_history=conversation_history
            )
            
            # Display response
            print(f"\n🤖 Cevap:\n{response['answer']}")
            
            # Show sources briefly
            if response['sources']:
                print(f"\n📚 Kaynaklar: {response['sources'][0]['title']}")
            
            # Update conversation history (optional)
            # conversation_history.append({"role": "user", "content": question})
            # conversation_history.append({"role": "assistant", "content": response['answer']})
            
            # Track cost
            cost = response['metadata']['cost']
            total_cost += cost
            print(f"💰 Maliyet: ${cost:.4f} (Toplam: ${total_cost:.4f})")
            print()
        
        except Exception as e:
            print(f"\n❌ Hata: {e}")
            import traceback
            traceback.print_exc()


def test_streaming():
    """Test 4: Streaming response."""
    print("\n" + "=" * 80)
    print("TEST 4: Streaming Response")
    print("=" * 80)
    
    # Check API key
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("\n⚠️ OpenAI API key not set!")
        return
    
    print("\n🤖 Initializing chatbot...")
    generator = ResponseGenerator()
    
    question = "Yüksek lisans programında azami süre ne kadardır?"
    
    print(f"\n❓ Soru: {question}")
    print("\n🤖 Cevap (streaming):")
    print("─" * 80)
    
    # Stream response
    for chunk in generator.generate_response_stream(question):
        print(chunk, end='', flush=True)
    
    print("\n" + "─" * 80)


def main():
    """Main test runner."""
    print("\n" + "=" * 80)
    print("MEVZUAT CHATBOT TEST")
    print("=" * 80)
    
    print("\nChoose test:")
    print("1. Single Question (quick test)")
    print("2. Multiple Questions (batch test)")
    print("3. Interactive Mode (chat)")
    print("4. Streaming Response")
    print("0. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_single_question()
    elif choice == "2":
        test_multiple_questions()
    elif choice == "3":
        interactive_mode()
    elif choice == "4":
        test_streaming()
    elif choice == "0":
        print("Exiting...")
        return
    else:
        print("Invalid choice. Running single question test...")
        test_single_question()
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
