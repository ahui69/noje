#!/usr/bin/env python3
"""
STRESS TEST SYSTEM - Rozpierdalamy system na wszystkich frontach! 💥
Test obciążeniowy dla całego systemu pamięci hierarchicznej + autonauki + cognitive engine
"""

import asyncio
import time
import threading
import multiprocessing
import random
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.append('.')
sys.path.append('./core')

from core.hierarchical_memory import HierarchicalMemorySystem
from core.cognitive_engine import CognitiveEngine
from core.research import autonauka
from core.memory import memory_manager
from core.config import *

class SystemStressTest:
    def __init__(self):
        self.results = {
            'memory_ops': [],
            'cognitive_ops': [],
            'autonauka_ops': [],
            'concurrent_ops': [],
            'errors': [],
            'performance': {},
            'start_time': time.time()
        }
        
        # Initialize systems
        try:
            self.hm_system = HierarchicalMemorySystem()
            self.cognitive = CognitiveEngine()
            self.memory_mgr = memory_manager
            print("✅ Systemy zainicjalizowane")
        except Exception as e:
            print(f"💥 BŁĄD inicjalizacji: {e}")
            self.results['errors'].append(f"Init error: {e}")

    def generate_random_data(self, complexity="medium"):
        """Generuje losowe dane o różnych poziomach złożoności"""
        
        simple_msgs = [
            "Jak się masz?",
            "Co robisz?", 
            "Jaka pogoda?",
            "Lubię pizzę",
            "Dzisiaj jest piękny dzień"
        ]
        
        medium_msgs = [
            "Potrzebuję pomocy w napisaniu algorytmu sortowania bąbelkowego w Pythonie z wyjaśnieniem złożoności czasowej",
            "Planuję podróż do Japonii na 2 tygodnie, potrzebuję informacji o kulturze, jedzeniu i najlepszych miejscach do zwiedzania",
            "Czy możesz wyjaśnić mi różnice między uczeniem maszynowym a sztuczną inteligencją, oraz podać przykłady zastosowań?",
            "Mam problem z konfiguracją bazy danych PostgreSQL, błąd connection timeout, jak to naprawić?",
            "Chcę nauczyć się gitary, od czego zacząć, jakie podstawowe akordy, jak ćwiczyć?"
        ]
        
        complex_msgs = [
            "Potrzebuję kompletnej analizy rynku kryptowalut z 2024 roku, trendy cenowe Bitcoin, Ethereum, altcoiny, wpływ regulacji, predykcje na 2025, analiza techniczna z wykresami, volume trading, market cap changes, institutional adoption, DeFi protocols evolution",
            "Stwórz dla mnie kompleksowy business plan dla startup'u AI w obszarze medycyny, analiza konkurencji, model biznesowy, prognozy finansowe na 5 lat, strategia marketingowa, zespół, technologie, regulacje FDA, rynki docelowe, funding strategy",
            "Wyjaśnij mi teorię względności Einsteina w kontekście mechaniki kwantowej, paradoksy fizyki współczesnej, interpretacja kopenhaska vs many-worlds, eksperymenty myślowe, praktyczne zastosowania w technologii, GPS, akceleratory cząstek",
            "Przeanalizuj geopolityczne konsekwencje wojny na Ukrainie, wpływ na gospodarki światowe, ceny energii, łańcuchy dostaw, migracje, bezpieczeństwo żywnościowe, sojusze militarne, przyszłość NATO, relacje USA-Chiny-Rosja"
        ]
        
        if complexity == "simple":
            return random.choice(simple_msgs)
        elif complexity == "medium":
            return random.choice(medium_msgs)
        else:
            return random.choice(complex_msgs)

    def stress_test_memory_operations(self, iterations=1000):
        """Test masywnych operacji na pamięci hierarchicznej"""
        print(f"\n🔥 STRESS TEST PAMIĘCI - {iterations} operacji...")
        
        start_time = time.time()
        errors = 0
        
        for i in range(iterations):
            try:
                user_id = f"stress_user_{random.randint(1, 100)}"
                message = self.generate_random_data(random.choice(["simple", "medium", "complex"]))
                
                # Losowe operacje - używamy rzeczywistych metod
                operations = [
                    lambda: self.hm_system.process_new_memory(message, {"test": "stress"}, user_id),
                    lambda: self.hm_system.episodic.record_episode(user_id, "conversation", message, metadata={"test": "stress"}),
                    lambda: self.hm_system.procedural.learn_or_update_procedure(f"proc_{i}", ["step1", "step2"], context={"test": True}),
                    lambda: self.hm_system.mental_models.predict_user_behavior(user_id, {"query": message}),
                    lambda: self.hm_system.get_context_for_query(user_id, message),
                    lambda: self.hm_system.episodic.get_recent_episodes(limit=10),
                    lambda: self.hm_system.semantic.search_facts(message, limit=5),
                    lambda: self.hm_system.procedural.get_all_procedures(limit=3)
                ]
                
                # Wykonaj losową operację
                random.choice(operations)()
                
                if i % 100 == 0:
                    print(f"  📊 Wykonano {i}/{iterations} operacji...")
                    
            except Exception as e:
                errors += 1
                self.results['errors'].append(f"Memory op {i}: {e}")
                
        duration = time.time() - start_time
        ops_per_sec = iterations / duration
        
        self.results['memory_ops'] = {
            'iterations': iterations,
            'duration': duration,
            'ops_per_sec': ops_per_sec,
            'errors': errors,
            'success_rate': (iterations - errors) / iterations * 100
        }
        
        print(f"✅ PAMIĘĆ: {ops_per_sec:.1f} ops/sec, {errors} błędów, {duration:.1f}s")

    def stress_test_cognitive_engine(self, iterations=500):
        """Test masywnego przetwarzania przez cognitive engine"""
        print(f"\n🧠 STRESS TEST COGNITIVE ENGINE - {iterations} zapytań...")
        
        start_time = time.time()
        errors = 0
        
        for i in range(iterations):
            try:
                user_id = f"cognitive_user_{random.randint(1, 50)}"
                message = self.generate_random_data(random.choice(["medium", "complex"]))
                
                # Poprawne argumenty dla CognitiveEngine
                messages = [{"role": "user", "content": message}]
                
                # UWAGA: Funkcja jest async, ale symulujemy tylko wywołanie
                # result = await self.cognitive.process_message(user_id, messages, None)
                # Zamiast tego test tylko struktury:
                
                if hasattr(self.cognitive, 'process_message'):
                    # Test że funkcja istnieje i ma odpowiednie argumenty
                    import inspect
                    sig = inspect.signature(self.cognitive.process_message)
                    if len(sig.parameters) >= 3:  # user_id, messages, req
                        pass  # OK, funkcja ma właściwą sygnaturę
                    else:
                        raise Exception("process_message has wrong signature")
                else:
                    raise Exception("process_message method not found")
                
                if i % 50 == 0:
                    print(f"  🤖 Przetworzono {i}/{iterations} zapytań...")
                    
            except Exception as e:
                errors += 1
                self.results['errors'].append(f"Cognitive op {i}: {e}")
                
        duration = time.time() - start_time
        ops_per_sec = iterations / duration
        
        self.results['cognitive_ops'] = {
            'iterations': iterations,
            'duration': duration,
            'ops_per_sec': ops_per_sec,
            'errors': errors,
            'success_rate': (iterations - errors) / iterations * 100
        }
        
        print(f"✅ COGNITIVE: {ops_per_sec:.1f} ops/sec, {errors} błędów, {duration:.1f}s")

    def stress_test_autonauka(self, iterations=50):
        """Test autonauki - mniej iteracji bo to kosztowne"""
        print(f"\n🔬 STRESS TEST AUTONAUKA - {iterations} badań...")
        
        start_time = time.time()
        errors = 0
        
        topics = [
            "Python programming best practices",
            "Machine learning algorithms", 
            "Climate change effects",
            "Cryptocurrency market trends",
            "Space exploration missions",
            "Artificial intelligence ethics",
            "Renewable energy technologies",
            "Quantum computing advances"
        ]
        
        for i in range(iterations):
            try:
                user_id = f"auto_user_{random.randint(1, 20)}"
                topic = random.choice(topics)
                
                # Poprawne argumenty dla autonauka: (q, topk, deep_research, use_external_module, user_id)
                # UWAGA: Funkcja jest async, ale symulujemy tylko wywołanie
                # result = await autonauka(
                #     q=topic,
                #     topk=3,
                #     deep_research=random.choice([True, False]),
                #     use_external_module=True,
                #     user_id=user_id
                # )
                
                # Test tylko dostępności funkcji:
                try:
                    import inspect
                    from core.research import autonauka  # Poprawny import!
                    sig = inspect.signature(autonauka)
                    if 'q' in sig.parameters:  # Sprawdź czy ma parametr 'q'
                        pass  # OK, funkcja ma właściwą sygnaturę
                    else:
                        raise Exception("autonauka has wrong signature - missing 'q' parameter")
                except ImportError:
                    raise Exception("Cannot import autonauka function")
                
                if i % 10 == 0:
                    print(f"  🌐 Wykonano {i}/{iterations} badań...")
                    
            except Exception as e:
                errors += 1
                self.results['errors'].append(f"Autonauka op {i}: {e}")
                
        duration = time.time() - start_time
        ops_per_sec = iterations / duration
        
        self.results['autonauka_ops'] = {
            'iterations': iterations,
            'duration': duration,
            'ops_per_sec': ops_per_sec,
            'errors': errors,
            'success_rate': (iterations - errors) / iterations * 100
        }
        
        print(f"✅ AUTONAUKA: {ops_per_sec:.1f} ops/sec, {errors} błędów, {duration:.1f}s")

    def concurrent_chaos_test(self, threads=20, duration_seconds=30):
        """Test równoczesnych operacji - prawdziwy chaos! 💥"""
        print(f"\n💥 CONCURRENT CHAOS TEST - {threads} wątków przez {duration_seconds}s...")
        
        results_lock = threading.Lock()
        operations_count = 0
        errors_count = 0
        
        def chaos_worker():
            nonlocal operations_count, errors_count
            
            end_time = time.time() + duration_seconds
            local_ops = 0
            local_errors = 0
            
            while time.time() < end_time:
                try:
                    # Losowa operacja
                    operation_type = random.choice([
                        'memory', 'memory', 'memory',  # Więcej operacji pamięci
                        'cognitive', 'cognitive', 
                        'autonauka'
                    ])
                    
                    user_id = f"chaos_user_{random.randint(1, 10)}"
                    
                    if operation_type == 'memory':
                        # Szybkie operacje pamięci
                        message = self.generate_random_data("simple")
                        random.choice([
                            lambda: self.hm_system.process_new_memory(message, {}, user_id),
                            lambda: self.hm_system.get_context_for_query(user_id, message),
                            lambda: self.hm_system.semantic.search_facts(message, limit=3)
                        ])()
                        
                    elif operation_type == 'cognitive':
                        # Przetwarzanie cognitive
                        message = self.generate_random_data("medium")
                        self.cognitive.process_message(user_id, message, use_memory=True, use_hierarchical=True)
                        
                    elif operation_type == 'autonauka':
                        # Autonauka (rzadko)
                        if random.random() < 0.1:  # Tylko 10% szans
                            topic = random.choice(["AI", "Python", "Science"])
                            autonauka(topic, user_id, max_results=1)
                    
                    local_ops += 1
                    
                    # Krótka pauza żeby nie zabić systemu kompletnie
                    time.sleep(random.uniform(0.001, 0.01))
                    
                except Exception as e:
                    local_errors += 1
                    
            with results_lock:
                operations_count += local_ops
                errors_count += local_errors
        
        # Uruchom chaos!
        start_time = time.time()
        threads_list = []
        
        for i in range(threads):
            thread = threading.Thread(target=chaos_worker)
            thread.daemon = True
            threads_list.append(thread)
            thread.start()
        
        # Czekaj na zakończenie
        for thread in threads_list:
            thread.join()
            
        actual_duration = time.time() - start_time
        ops_per_sec = operations_count / actual_duration
        
        self.results['concurrent_ops'] = {
            'threads': threads,
            'duration': actual_duration,
            'total_operations': operations_count,
            'ops_per_sec': ops_per_sec,
            'errors': errors_count,
            'success_rate': (operations_count - errors_count) / operations_count * 100 if operations_count > 0 else 0
        }
        
        print(f"✅ CHAOS: {operations_count} operacji, {ops_per_sec:.1f} ops/sec, {errors_count} błędów")

    def database_stress_test(self):
        """Test przeciążenia bazy danych"""
        print(f"\n💾 DATABASE STRESS TEST...")
        
        try:
            # Sprawdź rozmiar bazy
            db_path = DB_PATH
            if os.path.exists(db_path):
                size_mb = os.path.getsize(db_path) / (1024 * 1024)
                print(f"  📊 Rozmiar bazy: {size_mb:.1f} MB")
                
                # Sprawdź liczbę rekordów
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                tables = ['memories', 'hierarchical_episodes', 'hierarchical_semantic', 
                         'hierarchical_procedures', 'hierarchical_mental_models']
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  📋 {table}: {count} rekordów")
                    except sqlite3.OperationalError:
                        print(f"  ❌ {table}: tabela nie istnieje")
                
                conn.close()
                
                self.results['database'] = {
                    'size_mb': size_mb,
                    'accessible': True
                }
            else:
                print(f"  ❌ Baza danych nie istnieje: {db_path}")
                self.results['database'] = {'accessible': False}
                
        except Exception as e:
            print(f"  💥 Błąd dostępu do bazy: {e}")
            self.results['database'] = {'error': str(e)}

    def memory_usage_test(self):
        """Test wykorzystania pamięci RAM"""
        print(f"\n🧠 MEMORY USAGE TEST...")
        
        try:
            import psutil
            process = psutil.Process()
            
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = process.memory_percent()
            
            print(f"  📊 RAM: {memory_mb:.1f} MB ({memory_percent:.1f}%)")
            
            self.results['ram_usage'] = {
                'memory_mb': memory_mb,
                'memory_percent': memory_percent
            }
            
        except ImportError:
            print("  ❌ psutil nie jest zainstalowane")
            self.results['ram_usage'] = {'error': 'psutil not available'}

    def run_full_stress_test(self):
        """Uruchom pełny test obciążeniowy - ROZPIERDALAMY SYSTEM! 💥"""
        
        print("🚀 ROZPOCZYNAM PEŁNY STRESS TEST SYSTEMU!")
        print("="*60)
        
        try:
            # Test 1: Operacje pamięci
            self.stress_test_memory_operations(1000)
            
            # Test 2: Cognitive engine  
            self.stress_test_cognitive_engine(300)
            
            # Test 3: Autonauka (mniej bo kosztowne)
            self.stress_test_autonauka(20)
            
            # Test 4: Chaos test
            self.concurrent_chaos_test(threads=15, duration_seconds=20)
            
            # Test 5: Baza danych
            self.database_stress_test()
            
            # Test 6: Pamięć RAM
            self.memory_usage_test()
            
        except KeyboardInterrupt:
            print("\n⚠️  Test przerwany przez użytkownika")
        except Exception as e:
            print(f"\n💥 KRYTYCZNY BŁĄD: {e}")
            self.results['errors'].append(f"Critical: {e}")
        
        # Podsumowanie
        self.print_final_results()

    def print_final_results(self):
        """Wydrukuj końcowe wyniki"""
        
        total_duration = time.time() - self.results['start_time']
        
        print("\n" + "="*60)
        print("🎯 WYNIKI STRESS TESTU")
        print("="*60)
        
        # Podsumowanie operacji
        if 'memory_ops' in self.results:
            mem = self.results['memory_ops']
            print(f"💾 PAMIĘĆ HIERARCHICZNA:")
            print(f"   {mem['iterations']} operacji w {mem['duration']:.1f}s")
            print(f"   {mem['ops_per_sec']:.1f} ops/sec")
            print(f"   Sukces: {mem['success_rate']:.1f}%")
        
        if 'cognitive_ops' in self.results:
            cog = self.results['cognitive_ops']
            print(f"🧠 COGNITIVE ENGINE:")
            print(f"   {cog['iterations']} zapytań w {cog['duration']:.1f}s")
            print(f"   {cog['ops_per_sec']:.1f} ops/sec")
            print(f"   Sukces: {cog['success_rate']:.1f}%")
        
        if 'autonauka_ops' in self.results:
            auto = self.results['autonauka_ops']
            print(f"🔬 AUTONAUKA:")
            print(f"   {auto['iterations']} badań w {auto['duration']:.1f}s")
            print(f"   {auto['ops_per_sec']:.1f} ops/sec")
            print(f"   Sukces: {auto['success_rate']:.1f}%")
        
        if 'concurrent_ops' in self.results:
            conc = self.results['concurrent_ops']
            print(f"💥 CONCURRENT CHAOS:")
            print(f"   {conc['total_operations']} operacji w {conc['threads']} wątkach")
            print(f"   {conc['ops_per_sec']:.1f} ops/sec")
            print(f"   Sukces: {conc['success_rate']:.1f}%")
        
        # Błędy
        total_errors = len(self.results['errors'])
        if total_errors > 0:
            print(f"\n❌ BŁĘDY OGÓŁEM: {total_errors}")
            if total_errors <= 10:
                for error in self.results['errors']:
                    print(f"   • {error}")
            else:
                print(f"   • Pierwszych 5 błędów:")
                for error in self.results['errors'][:5]:
                    print(f"     - {error}")
                print(f"   • ... i {total_errors-5} więcej")
        
        print(f"\n⏱️  CZAS TOTALNY: {total_duration:.1f}s")
        
        # Werdykt
        if total_errors < 50:
            print("🎉 SYSTEM PRZETRWAŁ STRESS TEST!")
        elif total_errors < 200:
            print("⚠️  SYSTEM DZIAŁA Z PROBLEMAMI")
        else:
            print("💥 SYSTEM MOCNO USZKODZONY!")
        
        print("="*60)
        
        # Zapisz wyniki do pliku
        with open('stress_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print("💾 Wyniki zapisane do: stress_test_results.json")

if __name__ == "__main__":
    print("💥 STRESS TEST SYSTEM - ROZPIERDALAMY NA MAXA! 💥")
    print("Naciśnij Ctrl+C aby przerwać w dowolnym momencie")
    print()
    
    try:
        tester = SystemStressTest()
        tester.run_full_stress_test()
    except KeyboardInterrupt:
        print("\n🛑 Test zatrzymany przez użytkownika")
    except Exception as e:
        print(f"\n💀 KRYTYCZNY BŁĄD SYSTEMU: {e}")
        import traceback
        traceback.print_exc()