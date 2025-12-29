#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parallel Processing Module - Optymalizacja równoległego przetwarzania zapytań
Zaawansowane techniki współbieżności i obsługa puli wątków
"""

import asyncio
import concurrent.futures
import time
import functools
import logging
from typing import List, Dict, Any, Callable, TypeVar, Awaitable, Optional, Union, Tuple
from collections import deque

from .config import MAX_CONCURRENCY, PARALLEL_TIMEOUT, PRIORITY_LEVELS
from .helpers import log_info, log_warning, log_error

# Generyczny typ dla funkcji
T = TypeVar('T')
R = TypeVar('R')

# ═══════════════════════════════════════════════════════════════════
# ASYNCHRONICZNA PULA ZADAŃ Z PRIORYTETAMI
# ═══════════════════════════════════════════════════════════════════

class AsyncTaskPool:
    """
    Zaawansowana pula zadań asynchronicznych z obsługą priorytetów i limitem współbieżności
    """
    
    def __init__(self, max_workers: int = MAX_CONCURRENCY):
        """Inicjalizuje pulę zadań z maksymalną liczbą równoległych zadań"""
        self.max_workers = max_workers
        self.active_tasks = 0
        self.semaphore = asyncio.Semaphore(max_workers)
        self.task_queues = {priority: deque() for priority in range(PRIORITY_LEVELS)}
        self.event = asyncio.Event()
        self.running = False
        self.processor_task = None
        self._stats = {
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "avg_wait_time": 0.0,
            "avg_process_time": 0.0,
        }
    
    async def start(self):
        """Uruchamia przetwarzanie zadań"""
        if self.running:
            return
            
        self.running = True
        self.processor_task = asyncio.create_task(self._process_queue())
        log_info(f"AsyncTaskPool uruchomiony (max_workers={self.max_workers})", "PARALLEL")
        
    async def stop(self):
        """Zatrzymuje przetwarzanie zadań"""
        if not self.running:
            return
            
        self.running = False
        if self.processor_task:
            self.event.set()  # Obudź procesor kolejki
            await self.processor_task
            self.processor_task = None
        log_info("AsyncTaskPool zatrzymany", "PARALLEL")
    
    async def submit(self, func: Callable[..., Awaitable[T]], *args, 
                     priority: int = 1, timeout: float = PARALLEL_TIMEOUT, **kwargs) -> T:
        """
        Dodaje zadanie do puli z określonym priorytetem
        
        Args:
            func: Funkcja asynchroniczna do wykonania
            *args: Argumenty dla funkcji
            priority: Priorytet (0-wyższy, PRIORITY_LEVELS-1-niższy)
            timeout: Maksymalny czas wykonania w sekundach
            **kwargs: Argumenty nazwane dla funkcji
            
        Returns:
            Wynik funkcji
        """
        if not self.running:
            await self.start()
            
        priority = max(0, min(PRIORITY_LEVELS - 1, priority))
        task_future = asyncio.Future()
        submit_time = time.time()
        
        self._stats["submitted"] += 1
        self.task_queues[priority].append((func, args, kwargs, task_future, submit_time, timeout))
        self.event.set()  # Powiadom procesor o nowym zadaniu
        
        return await task_future
    
    async def _process_queue(self):
        """Główna pętla przetwarzania kolejki zadań"""
        while self.running:
            # Sprawdź czy są zadania w kolejce
            task_found = False
            
            # Sprawdź zadania według priorytetu
            for priority in range(PRIORITY_LEVELS):
                if self.task_queues[priority]:
                    task_found = True
                    
                    # Czekaj na dostępny slot
                    async with self.semaphore:
                        self.active_tasks += 1
                        try:
                            func, args, kwargs, future, submit_time, timeout = self.task_queues[priority].popleft()
                            
                            # Uruchom zadanie
                            wait_time = time.time() - submit_time
                            self._update_wait_stats(wait_time)
                            
                            start_time = time.time()
                            try:
                                result = await asyncio.wait_for(func(*args, **kwargs), timeout)
                                future.set_result(result)
                                self._stats["completed"] += 1
                            except asyncio.TimeoutError:
                                future.set_exception(TimeoutError(f"Zadanie przekroczyło timeout {timeout}s"))
                                log_warning(f"Zadanie {func.__name__} przekroczyło timeout {timeout}s", "PARALLEL")
                                self._stats["failed"] += 1
                            except Exception as e:
                                future.set_exception(e)
                                log_error(e, f"PARALLEL_{func.__name__}")
                                self._stats["failed"] += 1
                            finally:
                                self._update_process_stats(time.time() - start_time)
                        finally:
                            self.active_tasks -= 1
                    
                    break  # Przetworzono zadanie, wróć do najwyższego priorytetu
            
            # Jeśli nie ma zadań, czekaj na powiadomienie
            if not task_found:
                self.event.clear()
                try:
                    await asyncio.wait_for(self.event.wait(), 1.0)
                except asyncio.TimeoutError:
                    pass  # Okresowe budzenie do sprawdzenia warunków
    
    def _update_wait_stats(self, wait_time: float):
        """Aktualizuje statystyki czasu oczekiwania"""
        old_avg = self._stats["avg_wait_time"]
        old_count = self._stats["completed"] + self._stats["failed"]
        if old_count > 0:
            self._stats["avg_wait_time"] = (old_avg * old_count + wait_time) / (old_count + 1)
        else:
            self._stats["avg_wait_time"] = wait_time
            
    def _update_process_stats(self, process_time: float):
        """Aktualizuje statystyki czasu przetwarzania"""
        old_avg = self._stats["avg_process_time"]
        old_count = self._stats["completed"] + self._stats["failed"] - 1  # odejmij bieżące zadanie
        if old_count > 0:
            self._stats["avg_process_time"] = (old_avg * old_count + process_time) / (old_count + 1)
        else:
            self._stats["avg_process_time"] = process_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki puli zadań"""
        stats = dict(self._stats)
        stats["active"] = self.active_tasks
        stats["pending"] = sum(len(q) for q in self.task_queues.values())
        stats["utilization"] = self.active_tasks / self.max_workers if self.max_workers > 0 else 0
        return stats


# ═══════════════════════════════════════════════════════════════════
# WRAPPERS DLA ASYNCIO I CONCURRENT.FUTURES
# ═══════════════════════════════════════════════════════════════════

# Globalna pula wątków i zadań
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENCY)
task_pool = AsyncTaskPool()

async def run_in_thread(func: Callable[..., R], *args, **kwargs) -> R:
    """
    Uruchamia blokującą funkcję w puli wątków
    
    Args:
        func: Funkcja blokująca do wykonania
        *args, **kwargs: Argumenty dla funkcji
        
    Returns:
        Wynik funkcji
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool, 
        functools.partial(func, *args, **kwargs)
    )

async def parallel_map(func: Callable[[T], Awaitable[R]], items: List[T], 
                       max_concurrency: int = None) -> List[R]:
    """
    Równoległe mapowanie asynchronicznej funkcji na listę elementów
    
    Args:
        func: Asynchroniczna funkcja do wywołania dla każdego elementu
        items: Lista elementów do przetworzenia
        max_concurrency: Maksymalna liczba równoległych zadań (None = domyślna)
        
    Returns:
        Lista wyników
    """
    if not items:
        return []
        
    if max_concurrency is None:
        max_concurrency = MAX_CONCURRENCY
        
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_item(item):
        async with semaphore:
            return await func(item)
            
    return await asyncio.gather(*[process_item(item) for item in items])
    
async def priority_parallel_map(func: Callable[[T], Awaitable[R]], items: List[Tuple[T, int]], 
                                timeout: float = PARALLEL_TIMEOUT) -> List[R]:
    """
    Równoległe mapowanie z obsługą priorytetów
    
    Args:
        func: Asynchroniczna funkcja do wywołania dla każdego elementu
        items: Lista krotek (element, priorytet)
        timeout: Maksymalny czas wykonania pojedynczej funkcji
        
    Returns:
        Lista wyników w kolejności zgodnej z input items
    """
    if not items:
        return []
        
    results = []
    tasks = []
    
    for i, (item, priority) in enumerate(items):
        task = asyncio.create_task(task_pool.submit(
            func, item, priority=priority, timeout=timeout
        ))
        tasks.append(task)
        
    for task in tasks:
        results.append(await task)
        
    return results

# Inicjalizacja puli zadań
async def initialize():
    """Inicjalizuje pule zadań"""
    await task_pool.start()
    log_info("Moduł przetwarzania równoległego zainicjalizowany", "PARALLEL")

# ═══════════════════════════════════════════════════════════════════
# WYSOKOPOZIOMOWE FUNKCJE UŻYTKOWE
# ═══════════════════════════════════════════════════════════════════

async def batch_process(items: List[T], processor: Callable[[T], Awaitable[R]], 
                        batch_size: int = 10, delay_between_batches: float = 0.1) -> List[R]:
    """
    Przetwarza elementy w partiach z zadanym opóźnieniem między partiami
    
    Args:
        items: Lista elementów do przetworzenia
        processor: Asynchroniczna funkcja przetwarzająca
        batch_size: Rozmiar partii
        delay_between_batches: Opóźnienie między partiami w sekundach
        
    Returns:
        Lista wyników
    """
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await parallel_map(processor, batch)
        results.extend(batch_results)
        
        if i + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)
            
    return results

async def process_with_fallback(primary_func: Callable[..., Awaitable[R]], 
                               fallback_func: Callable[..., Awaitable[R]], 
                               *args, max_retries: int = 3, **kwargs) -> R:
    """
    Próbuje wykonać funkcję podstawową, w przypadku błędu przełącza na zapasową
    
    Args:
        primary_func: Podstawowa funkcja asynchroniczna
        fallback_func: Zapasowa funkcja asynchroniczna
        *args, **kwargs: Argumenty dla funkcji
        max_retries: Maksymalna liczba ponownych prób dla primary_func
        
    Returns:
        Wynik funkcji (primary_func lub fallback_func)
    """
    retry_count = 0
    while retry_count <= max_retries:
        try:
            if retry_count == 0:
                return await primary_func(*args, **kwargs)
            else:
                log_warning(f"Ponawianie {retry_count}/{max_retries}: {primary_func.__name__}", "PARALLEL")
                return await asyncio.wait_for(primary_func(*args, **kwargs), PARALLEL_TIMEOUT)
        except (asyncio.TimeoutError, Exception) as e:
            retry_count += 1
            if retry_count > max_retries:
                log_warning(f"Przełączam na funkcję zapasową po {max_retries} błędach: {e}", "PARALLEL")
                return await fallback_func(*args, **kwargs)
            await asyncio.sleep(0.1 * (2 ** retry_count))  # Eksponencjalny backoff

# Dodaj wymagane stałe do konfiguracji
if not hasattr(concurrent.futures.ThreadPoolExecutor, "_max_workers"):
    concurrent.futures.ThreadPoolExecutor._max_workers = MAX_CONCURRENCY