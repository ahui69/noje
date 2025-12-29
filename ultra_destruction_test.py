#!/usr/bin/env python3
"""
🔥💀 ULTRA EKSTREMALNE ROZPIERDALANIE SYSTEMU 💀🔥
Ten test ma za zadanie kompletnie rozjechać system na wszystkich możliwych frontach!
UWAGA: To jest test destrukcyjny - może uszkodzić system!
"""

import asyncio
import time
import threading
import multiprocessing
import random
import json
import sqlite3
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
import sys
import os
import traceback
import signal

# Dodaj ścieżkę do modułów
sys.path.append('.')
sys.path.append('./core')

from core.hierarchical_memory import HierarchicalMemorySystem
from core.cognitive_engine import CognitiveEngine
from core.research import autonauka
from core.memory import memory_manager
from core.config import *

class UltraExtremeStressTest:
    def __init__(self):
        self.results = {
            'destruction_level': 0,  # 0-100 jak bardzo system został zniszczony
            'operations_completed': 0,
            'operations_failed': 0,
            'memory_leaks': [],
            'crashes': [],
            'database_corruption': False,
            'system_recovery_time': 0,
            'max_memory_usage': 0,
            'max_cpu_usage': 0,
            'start_time': time.time(),
            'test_phases': []
        }
        
        # Inicjalizuj systemy
        try:
            self.hm_system = HierarchicalMemorySystem()
            self.cognitive = CognitiveEngine()
            self.memory_mgr = memory_manager
            print("🔥 SYSTEMY ZAINICJALIZOWANE - PRZYGOTOWANIE DO DESTRUKCJI!")
        except Exception as e:
            print(f"💀 BŁĄD KRYTYCZNY już przy inicjalizacji: {e}")
            self.results['crashes'].append(f"Init crash: {e}")

    def generate_chaos_data(self, intensity="EXTREME"):
        """Generuje skrajnie chaotyczne dane o różnych poziomach destrukcji"""
        
        if intensity == "NORMAL":
            return random.choice([
                "Test message",
                "Simple query", 
                "Hello world",
                "Basic data"
            ])
        elif intensity == "HEAVY":
            return random.choice([
                "A" * random.randint(1000, 5000),  # Długie stringi
                "🔥💥🚀" * random.randint(100, 500),  # Emoji spam
                "SELECT * FROM " + "x" * 1000,  # SQL injection attempt
                "\n\r\t" * random.randint(50, 200),  # Whitespace chaos
                "{'malformed': json, 'test': " + str(random.random()),  # Broken JSON
                "\\x00\\x01\\x02" * random.randint(10, 100)  # Binary chaos
            ])
        else:  # EXTREME
            chaos_types = [
                # Memory bombs
                "X" * random.randint(10000, 100000),
                
                # Unicode chaos
                "".join([chr(random.randint(0, 65535)) for _ in range(random.randint(100, 1000))]),
                
                # Nested chaos
                json.dumps({"level_" + str(i): "data_" * random.randint(100, 500) for i in range(random.randint(10, 100))}),
                
                # SQL injection attempts
                "'; DROP TABLE users; --",
                "UNION SELECT * FROM sqlite_master",
                
                # Stack overflow attempts
                "(" * random.randint(1000, 5000) + ")" * random.randint(1000, 5000),
                
                # Regex bombs
                "a" * random.randint(1000, 5000) + "a?" * random.randint(100, 500),
                
                # Path traversal
                "../" * random.randint(50, 200) + "etc/passwd",
                
                # Format string attacks
                "%s" * random.randint(100, 500) + "%x" * random.randint(100, 500),
                
                # Buffer overflow simulation
                "AAAA" + "\\x41" * random.randint(1000, 5000),
                
                # Compression bombs (text)
                "0" * random.randint(50000, 200000),
                
                # Control character chaos
                "".join([chr(random.randint(0, 31)) for _ in range(random.randint(100, 500))]),
            ]
            
            return random.choice(chaos_types)

    def memory_bomb_test(self, bombs=50):
        """Test pamięciowych bomb - próba wyczerpania RAM"""
        print(f"\n💣 MEMORY BOMB TEST - {bombs} bomb...")
        
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        bombs_detonated = 0
        
        for i in range(bombs):
            try:
                # Twórz ogromne dane
                chaos_data = self.generate_chaos_data("EXTREME")
                user_id = f"bomb_user_{random.randint(1, 5)}"
                
                # Próbuj zapisać w pamięci hierarchicznej
                self.hm_system.process_new_memory(chaos_data, {"bomb": i}, user_id)
                
                bombs_detonated += 1
                
                # Sprawdź wykorzystanie pamięci
                current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                self.results['max_memory_usage'] = max(self.results['max_memory_usage'], current_memory)
                
                if current_memory - start_memory > 500:  # 500MB wzrost
                    print(f"  💀 MEMORY LEAK DETECTED: {current_memory - start_memory:.1f}MB")
                    self.results['memory_leaks'].append({
                        'bomb': i,
                        'memory_increase': current_memory - start_memory,
                        'timestamp': time.time()
                    })
                
                if i % 10 == 0:
                    print(f"  💣 {i}/{bombs} bomb detonated, RAM: {current_memory:.1f}MB")
                    
            except Exception as e:
                self.results['operations_failed'] += 1
                if "memory" in str(e).lower() or "overflow" in str(e).lower():
                    self.results['crashes'].append(f"Memory bomb {i}: {e}")
                    
        self.results['operations_completed'] += bombs_detonated
        end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        print(f"💥 MEMORY BOMBS: {bombs_detonated}/{bombs} detonated")
        print(f"📊 RAM: {start_memory:.1f}MB → {end_memory:.1f}MB (+{end_memory-start_memory:.1f}MB)")

    def database_corruption_test(self):
        """Test próbujący skorumpować bazę danych"""
        print(f"\n💾💀 DATABASE CORRUPTION TEST...")
        
        corruption_attempts = [
            # SQL injection attempts
            "'; DROP TABLE hierarchical_episodes; --",
            "UNION SELECT sql FROM sqlite_master",
            
            # Binary chaos
            b'\x00\x01\x02\x03\x04\x05' * 1000,
            
            # Oversized data
            "CORRUPT" * 100000,
            
            # NULL byte injection
            "test\x00corruption\x00data",
            
            # Unicode exploitation
            "\uFEFF" * 1000 + "corruption_test",
        ]
        
        corruptions_attempted = 0
        corruptions_successful = 0
        
        for i, corruption in enumerate(corruption_attempts):
            try:
                user_id = f"corrupt_user_{i}"
                
                # Próbuj zapisać skorumpowane dane
                result = self.hm_system.process_new_memory(
                    str(corruption) if isinstance(corruption, bytes) else corruption, 
                    {"corruption_test": True}, 
                    user_id
                )
                
                corruptions_attempted += 1
                
                # Sprawdź czy baza nadal działa
                try:
                    test_query = self.hm_system.get_context_for_query(user_id, "test")
                    if not test_query:
                        print(f"  💀 POSSIBLE DATABASE CORRUPTION detected after attempt {i}")
                        corruptions_successful += 1
                        self.results['database_corruption'] = True
                except Exception as db_e:
                    print(f"  🔥 DATABASE ERROR after corruption attempt {i}: {db_e}")
                    corruptions_successful += 1
                    self.results['database_corruption'] = True
                    
            except Exception as e:
                self.results['operations_failed'] += 1
                if "database" in str(e).lower() or "sqlite" in str(e).lower():
                    print(f"  💥 Database corruption attempt {i} caused: {e}")
                    corruptions_successful += 1
        
        self.results['operations_completed'] += corruptions_attempted
        print(f"💾 DATABASE CORRUPTION: {corruptions_successful}/{len(corruption_attempts)} successful")

    def infinite_recursion_test(self):
        """Test nieskończonej rekursji - próba przepełnienia stosu"""
        print(f"\n♾️💀 INFINITE RECURSION TEST...")
        
        def recursive_chaos(depth=0, max_depth=10000):
            """Nieskończona rekursja z chaosem"""
            if depth >= max_depth:
                return "MAX_DEPTH_REACHED"
                
            try:
                # Twórz chaos na każdym poziomie
                chaos_data = self.generate_chaos_data("HEAVY")
                user_id = f"recursive_user_{depth % 10}"
                
                # Zapisz w pamięci
                self.hm_system.process_new_memory(
                    f"Recursion level {depth}: {chaos_data[:100]}", 
                    {"recursion_depth": depth}, 
                    user_id
                )
                
                # Rekursywnie wywołaj siebie
                return recursive_chaos(depth + 1, max_depth)
                
            except RecursionError as re:
                print(f"  💀 RECURSION LIMIT HIT at depth {depth}")
                self.results['crashes'].append(f"Recursion limit: depth {depth}")
                return f"RECURSION_ERROR_AT_{depth}"
            except Exception as e:
                self.results['operations_failed'] += 1
                return f"ERROR_AT_{depth}: {e}"
        
        try:
            result = recursive_chaos()
            self.results['operations_completed'] += 1
            print(f"♾️ RECURSION TEST: {result}")
        except Exception as e:
            print(f"💥 RECURSION TEST CRASHED: {e}")
            self.results['crashes'].append(f"Recursion test: {e}")

    def thread_bomb_test(self, threads=100, duration=30):
        """Test bomby wątkowej - próba wyczerpania zasobów systemowych"""
        print(f"\n🧵💣 THREAD BOMB TEST - {threads} wątków przez {duration}s...")
        
        results_lock = threading.Lock()
        thread_operations = 0
        thread_crashes = 0
        active_threads = []
        
        def thread_chaos_worker(thread_id):
            nonlocal thread_operations, thread_crashes
            
            local_ops = 0
            local_crashes = 0
            end_time = time.time() + duration
            
            while time.time() < end_time:
                try:
                    operation_type = random.choice([
                        'memory_chaos', 'memory_chaos', 'memory_chaos',  # Więcej chaosu pamięci
                        'cognitive_overload', 
                        'autonauka_spam',
                        'database_spam'
                    ])
                    
                    user_id = f"thread_{thread_id}_user_{random.randint(1, 5)}"
                    chaos_data = self.generate_chaos_data(random.choice(["HEAVY", "EXTREME"]))
                    
                    if operation_type == 'memory_chaos':
                        self.hm_system.process_new_memory(chaos_data, {"thread_chaos": thread_id}, user_id)
                        
                    elif operation_type == 'cognitive_overload':
                        self.cognitive.process_message(user_id, chaos_data, use_memory=True, use_hierarchical=True)
                        
                    elif operation_type == 'autonauka_spam':
                        if random.random() < 0.05:  # 5% szans - rzadko bo kosztowne
                            autonauka(chaos_data[:50], user_id, max_results=1)
                            
                    elif operation_type == 'database_spam':
                        context = self.hm_system.get_context_for_query(user_id, chaos_data[:100])
                    
                    local_ops += 1
                    
                    # Agresywne tempo - bez pauzy!
                    
                except Exception as e:
                    local_crashes += 1
                    
            with results_lock:
                thread_operations += local_ops
                thread_crashes += local_crashes
        
        # Uruchom bombę wątków!
        start_time = time.time()
        
        for i in range(threads):
            thread = threading.Thread(target=thread_chaos_worker, args=(i,), daemon=True)
            active_threads.append(thread)
            thread.start()
            
            # Mikro-pauza żeby nie zabić systemu całkowicie
            time.sleep(0.001)
        
        # Monitoruj CPU podczas testu
        cpu_samples = []
        def monitor_cpu():
            while time.time() < start_time + duration + 5:
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_samples.append(cpu_percent)
                self.results['max_cpu_usage'] = max(self.results['max_cpu_usage'], cpu_percent)
                
        cpu_monitor = threading.Thread(target=monitor_cpu, daemon=True)
        cpu_monitor.start()
        
        # Czekaj na zakończenie
        for thread in active_threads:
            thread.join(timeout=duration + 10)
            
        actual_duration = time.time() - start_time
        
        self.results['operations_completed'] += thread_operations
        self.results['operations_failed'] += thread_crashes
        
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        
        print(f"🧵 THREAD BOMB: {thread_operations} operacji, {thread_crashes} crashy")
        print(f"⚡ CPU: avg {avg_cpu:.1f}%, max {self.results['max_cpu_usage']:.1f}%")

    def system_recovery_test(self):
        """Test odzyskiwania systemu po ataku"""
        print(f"\n🔄💚 SYSTEM RECOVERY TEST...")
        
        recovery_start = time.time()
        
        try:
            # Próbuj oczyszczenie pamięci
            gc.collect()
            
            # Test podstawowych funkcji
            test_user = "recovery_test_user"
            test_message = "System recovery test message"
            
            # Test pamięci hierarchicznej
            recovery_result = self.hm_system.process_new_memory(
                test_message, 
                {"recovery_test": True}, 
                test_user
            )
            
            # Test cognitive engine
            cognitive_result = self.cognitive.process_message(
                test_user, 
                test_message, 
                use_memory=True,
                use_hierarchical=True
            )
            
            # Test kontekstu
            context_result = self.hm_system.get_context_for_query(test_user, test_message)
            
            recovery_time = time.time() - recovery_start
            self.results['system_recovery_time'] = recovery_time
            
            # Sprawdź czy system się odzyskał
            if recovery_result and context_result:
                print(f"✅ SYSTEM RECOVERED in {recovery_time:.2f}s")
                return True
            else:
                print(f"❌ SYSTEM FAILED TO RECOVER")
                return False
                
        except Exception as e:
            recovery_time = time.time() - recovery_start
            self.results['system_recovery_time'] = recovery_time
            print(f"💀 SYSTEM RECOVERY FAILED: {e}")
            self.results['crashes'].append(f"Recovery failed: {e}")
            return False

    def calculate_destruction_level(self):
        """Oblicza poziom zniszczenia systemu 0-100"""
        destruction = 0
        
        # Crashe (30 punktów max)
        destruction += min(len(self.results['crashes']) * 5, 30)
        
        # Memory leaks (20 punktów max)
        destruction += min(len(self.results['memory_leaks']) * 10, 20)
        
        # Database corruption (25 punktów max)
        if self.results['database_corruption']:
            destruction += 25
        
        # Failure rate (15 punktów max)
        total_ops = self.results['operations_completed'] + self.results['operations_failed']
        if total_ops > 0:
            failure_rate = self.results['operations_failed'] / total_ops
            destruction += min(failure_rate * 15, 15)
        
        # Recovery time (10 punktów max)
        if self.results['system_recovery_time'] > 10:
            destruction += 10
        elif self.results['system_recovery_time'] > 5:
            destruction += 5
        
        self.results['destruction_level'] = min(destruction, 100)
        return self.results['destruction_level']

    def run_ultra_extreme_test(self):
        """Uruchom ULTRA EKSTREMALNY test destrukcyjny! 💀🔥"""
        
        print("🔥💀" + "="*60 + "💀🔥")
        print("💥 ROZPOCZYNAM ULTRA EKSTREMALNE ROZPIERDALANIE SYSTEMU! 💥")
        print("🚨 UWAGA: Test może uszkodzić system! 🚨")
        print("🔥💀" + "="*60 + "💀🔥")
        
        try:
            # Faza 1: Memory Bombs
            phase_start = time.time()
            self.memory_bomb_test(30)
            self.results['test_phases'].append({
                'phase': 'Memory Bombs',
                'duration': time.time() - phase_start,
                'status': 'completed'
            })
            
            # Faza 2: Database Corruption  
            phase_start = time.time()
            self.database_corruption_test()
            self.results['test_phases'].append({
                'phase': 'Database Corruption',
                'duration': time.time() - phase_start,
                'status': 'completed'
            })
            
            # Faza 3: Infinite Recursion
            phase_start = time.time()
            self.infinite_recursion_test()
            self.results['test_phases'].append({
                'phase': 'Infinite Recursion',
                'duration': time.time() - phase_start,
                'status': 'completed'
            })
            
            # Faza 4: Thread Bomb (NAJGROŹNIEJSZA)
            phase_start = time.time()
            self.thread_bomb_test(threads=50, duration=15)  # Mniej agresywne żeby nie zabić systemu
            self.results['test_phases'].append({
                'phase': 'Thread Bomb',
                'duration': time.time() - phase_start,
                'status': 'completed'
            })
            
            # Faza 5: System Recovery
            phase_start = time.time()
            recovery_success = self.system_recovery_test()
            self.results['test_phases'].append({
                'phase': 'System Recovery',
                'duration': time.time() - phase_start,
                'status': 'success' if recovery_success else 'failed'
            })
            
        except KeyboardInterrupt:
            print("\n🛑 TEST PRZERWANY PRZEZ UŻYTKOWNIKA!")
            self.results['crashes'].append("User interrupted")
        except Exception as e:
            print(f"\n💀 KRYTYCZNY CRASH PODCZAS TESTU: {e}")
            self.results['crashes'].append(f"Critical test crash: {e}")
            traceback.print_exc()
        
        # Oblicz poziom zniszczenia
        destruction_level = self.calculate_destruction_level()
        
        # Podsumowanie
        self.print_destruction_report(destruction_level)

    def print_destruction_report(self, destruction_level):
        """Wydrukuj raport zniszczenia systemu"""
        
        total_duration = time.time() - self.results['start_time']
        
        print("\n" + "💀🔥" + "="*60 + "🔥💀")
        print("💥 RAPORT ZNISZCZENIA SYSTEMU 💥")
        print("💀🔥" + "="*60 + "🔥💀")
        
        # Poziom zniszczenia
        print(f"\n🎯 POZIOM ZNISZCZENIA: {destruction_level:.1f}/100")
        
        if destruction_level < 20:
            print("✅ SYSTEM PRZETRWAŁ - Lekkie uszkodzenia")
        elif destruction_level < 40:
            print("⚠️  SYSTEM USZKODZONY - Średnie zniszczenia")
        elif destruction_level < 70:
            print("🔥 SYSTEM MOCNO USZKODZONY - Poważne problemy")
        else:
            print("💀 SYSTEM CAŁKOWICIE ZNISZCZONY - Totalna destrukcja")
        
        # Statystyki operacji
        total_ops = self.results['operations_completed'] + self.results['operations_failed']
        success_rate = (self.results['operations_completed'] / total_ops * 100) if total_ops > 0 else 0
        
        print(f"\n📊 STATYSTYKI OPERACJI:")
        print(f"   ✅ Ukończone: {self.results['operations_completed']}")
        print(f"   ❌ Nieudane: {self.results['operations_failed']}")
        print(f"   📈 Sukces: {success_rate:.1f}%")
        
        # Crashe
        if self.results['crashes']:
            print(f"\n💥 CRASHE ({len(self.results['crashes'])}):")
            for i, crash in enumerate(self.results['crashes'][:5]):  # Top 5
                print(f"   {i+1}. {crash}")
            if len(self.results['crashes']) > 5:
                print(f"   ... i {len(self.results['crashes']) - 5} więcej")
        
        # Memory leaks
        if self.results['memory_leaks']:
            print(f"\n🧠 MEMORY LEAKS ({len(self.results['memory_leaks'])}):")
            for leak in self.results['memory_leaks'][:3]:
                print(f"   💧 Bomb {leak['bomb']}: +{leak['memory_increase']:.1f}MB")
        
        # Database corruption
        if self.results['database_corruption']:
            print(f"\n💾 DATABASE CORRUPTION: ❌ DETECTED")
        else:
            print(f"\n💾 DATABASE CORRUPTION: ✅ None detected")
        
        # System resources
        print(f"\n⚡ ZASOBY SYSTEMOWE:")
        print(f"   🧠 Max RAM: {self.results['max_memory_usage']:.1f}MB")
        print(f"   🔥 Max CPU: {self.results['max_cpu_usage']:.1f}%")
        print(f"   🔄 Recovery time: {self.results['system_recovery_time']:.2f}s")
        
        # Fazy testów
        print(f"\n🔄 FAZY TESTÓW:")
        for phase in self.results['test_phases']:
            status_icon = "✅" if phase['status'] == 'completed' else "❌" if phase['status'] == 'failed' else "⚠️"
            print(f"   {status_icon} {phase['phase']}: {phase['duration']:.1f}s")
        
        print(f"\n⏱️  CZAS TOTALNY: {total_duration:.1f}s")
        
        # Werdykt końcowy
        print(f"\n" + "🎭 WERDYKT KOŃCOWY 🎭")
        if destruction_level >= 80:
            print("💀 MISSION ACCOMPLISHED - SYSTEM ZOSTAŁ ROZPIERDALONY!")
        elif destruction_level >= 60:
            print("🔥 GOOD JOB - System mocno zniszczony!")
        elif destruction_level >= 40:
            print("⚠️  NOT BAD - System uszkodzony, ale wytrzymał")
        else:
            print("😤 SYSTEM TOO STRONG - Potrzeba więcej siły!")
        
        print("💀🔥" + "="*60 + "🔥💀")
        
        # Zapisz wyniki
        with open('ultra_destruction_report.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print("💾 Raport zniszczenia zapisany do: ultra_destruction_report.json")

if __name__ == "__main__":
    print("💀🔥 ULTRA EXTREME DESTRUCTION TEST 🔥💀")
    print("⚠️  UWAGA: Ten test może nieodwracalnie uszkodzić system!")
    print("Naciśnij Ctrl+C aby przerwać w dowolnym momencie")
    print()
    
    # Ostrzeżenie
    confirmation = input("🚨 Czy naprawdę chcesz rozpierdalić system? (wpisz 'DESTROY'): ")
    if confirmation != "DESTROY":
        print("❌ Test anulowany. Mądra decyzja!")
        sys.exit(0)
    
    print("\n💥 ROZPOCZYNAM DESTRUKCJĘ W 3... 2... 1... 💥")
    time.sleep(3)
    
    try:
        destroyer = UltraExtremeStressTest()
        destroyer.run_ultra_extreme_test()
    except KeyboardInterrupt:
        print("\n🛑 DESTRUKCJA ZATRZYMANA PRZEZ UŻYTKOWNIKA")
    except Exception as e:
        print(f"\n💀 KRYTYCZNY BŁĄD DESTRUCTORA: {e}")
        traceback.print_exc()