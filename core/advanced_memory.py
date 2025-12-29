#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Long-Term Memory Module - Zaawansowane operacje na pamięci długoterminowej
"""

import time
import json
import math
import sqlite3
import numpy as np
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from collections import defaultdict

from .config import DB_PATH, LTM_IMPORTANCE_THRESHOLD, LTM_CACHE_SIZE
from .helpers import log_info, log_warning, log_error, tokenize, make_id
from .parallel import parallel_map, task_pool
from .memory import ltm_add as _basic_ltm_add, ltm_search_hybrid as _basic_search

# ═══════════════════════════════════════════════════════════════════
# ZAAWANSOWANE STRUKTURY PAMIĘCI
# ═══════════════════════════════════════════════════════════════════

class MemoryNode:
    """Węzeł w grafie pamięci przechowujący pojedynczy fakt/wspomnienie"""
    
    def __init__(self, text: str, tags: List[str] = None, confidence: float = 0.7,
                 importance: float = 0.5, created_at: float = None):
        """
        Inicjalizuje węzeł pamięci
        
        Args:
            text: Treść faktu
            tags: Lista tagów
            confidence: Pewność faktu (0-1)
            importance: Ważność faktu (0-1)
            created_at: Czas utworzenia (timestamp)
        """
        self.id = make_id(text)
        self.text = text
        self.tags = tags or []
        self.confidence = max(0.0, min(1.0, confidence))
        self.importance = max(0.0, min(1.0, importance))
        self.created_at = created_at or time.time()
        self.accessed_at = time.time()
        self.access_count = 0
        self.connections = {}  # id -> siła powiązania (0-1)
        
    def access(self) -> None:
        """Aktualizuje statystyki dostępu"""
        self.accessed_at = time.time()
        self.access_count += 1
        
    def connect(self, other_id: str, strength: float = 0.5) -> None:
        """
        Tworzy lub wzmacnia połączenie z innym węzłem
        
        Args:
            other_id: ID węzła do połączenia
            strength: Siła połączenia (0-1)
        """
        current = self.connections.get(other_id, 0.0)
        # Połączenia wzmacniają się z czasem, ale nie przekraczają 1.0
        self.connections[other_id] = min(1.0, current + (strength * (1.0 - current)))
    
    def decay_connections(self, rate: float = 0.05) -> None:
        """
        Osłabia połączenia, które nie są aktywne
        
        Args:
            rate: Współczynnik osłabienia (0-1)
        """
        for node_id in list(self.connections.keys()):
            self.connections[node_id] *= (1.0 - rate)
            if self.connections[node_id] < 0.1:
                del self.connections[node_id]
                
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje węzeł do słownika"""
        return {
            "id": self.id,
            "text": self.text,
            "tags": self.tags,
            "confidence": self.confidence,
            "importance": self.importance,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "connections": self.connections
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryNode':
        """Tworzy węzeł ze słownika"""
        node = cls(
            text=data["text"],
            tags=data.get("tags", []),
            confidence=data.get("confidence", 0.7),
            importance=data.get("importance", 0.5),
            created_at=data.get("created_at", time.time())
        )
        node.id = data.get("id", node.id)
        node.accessed_at = data.get("accessed_at", node.accessed_at)
        node.access_count = data.get("access_count", 0)
        node.connections = data.get("connections", {})
        return node


class AssociativeMemory:
    """Pamięć asocjacyjna z grafem powiązań między faktami"""
    
    def __init__(self, max_nodes: int = LTM_CACHE_SIZE):
        """
        Inicjalizuje pamięć asocjacyjną
        
        Args:
            max_nodes: Maksymalna liczba węzłów w pamięci
        """
        self.nodes = {}  # id -> MemoryNode
        self.max_nodes = max_nodes
        self.tag_index = defaultdict(set)  # tag -> {node_ids}
        self.last_cleanup = time.time()
        
    def add(self, text: str, tags: List[str] = None, confidence: float = 0.7,
            importance: float = None) -> str:
        """
        Dodaje nowy fakt do pamięci
        
        Args:
            text: Treść faktu
            tags: Lista tagów
            confidence: Pewność faktu (0-1)
            importance: Ważność faktu (0-1), jeśli None to zostanie obliczona
            
        Returns:
            ID dodanego faktu
        """
        if importance is None:
            # Oblicz ważność na podstawie długości i innych czynników
            tokens = tokenize(text)
            length_factor = min(len(tokens) / 50, 1.0)  # Dłuższe teksty są ważniejsze
            importance = 0.5 + (length_factor * 0.3) + (confidence * 0.2)
        
        node = MemoryNode(text, tags, confidence, importance)
        
        # Sprawdź czy już istnieje
        existing_id = make_id(text)
        if existing_id in self.nodes:
            # Zaktualizuj istniejący węzeł
            existing = self.nodes[existing_id]
            existing.confidence = max(existing.confidence, confidence)
            existing.importance = max(existing.importance, importance or 0.0)
            if tags:
                existing.tags = list(set(existing.tags + tags))
            existing.access()
            return existing.id
            
        # Dodaj nowy węzeł
        self.nodes[node.id] = node
        
        # Zaktualizuj indeks tagów
        for tag in node.tags:
            self.tag_index[tag].add(node.id)
            
        # Połącz z powiązanymi węzłami na podstawie tagów
        self._create_connections(node)
        
        # Sprawdź czy nie przekroczono limitu węzłów
        if len(self.nodes) > self.max_nodes:
            self._cleanup_least_important()
            
        # Zapisz do bazy danych
        self._save_to_db(node)
            
        return node.id
    
    def _create_connections(self, node: MemoryNode) -> None:
        """
        Tworzy połączenia między nowym węzłem a istniejącymi
        
        Args:
            node: Nowy węzeł
        """
        # Znajdź powiązane węzły na podstawie tagów
        related_ids = set()
        for tag in node.tags:
            related_ids.update(self.tag_index.get(tag, set()))
        
        # Wyklucz sam węzeł
        if node.id in related_ids:
            related_ids.remove(node.id)
            
        # Utwórz połączenia
        for related_id in related_ids:
            if related_id in self.nodes:
                related = self.nodes[related_id]
                # Siła połączenia zależy od liczby wspólnych tagów
                common_tags = set(node.tags) & set(related.tags)
                strength = min(1.0, len(common_tags) / max(1, min(len(node.tags), len(related.tags))))
                
                # Wzajemne połączenia
                node.connect(related_id, strength)
                related.connect(node.id, strength)
    
    def _cleanup_least_important(self) -> None:
        """Usuwa najmniej ważne węzły gdy przekroczono limit"""
        if len(self.nodes) <= self.max_nodes:
            return
            
        # Oblicz "combined score" dla każdego węzła
        # score = importance * confidence * recency_factor * connectivity
        node_scores = {}
        current_time = time.time()
        
        for node_id, node in self.nodes.items():
            recency = 1.0 / (1.0 + 0.01 * (current_time - node.accessed_at) / 3600)  # Godziny
            connectivity = min(1.0, 0.1 + (0.3 * len(node.connections)))
            access_boost = min(1.0, node.access_count / 10)  # Boost dla często używanych
            
            score = (node.importance * 0.4 +
                     node.confidence * 0.2 +
                     recency * 0.15 +
                     connectivity * 0.15 +
                     access_boost * 0.1)
                     
            node_scores[node_id] = score
            
        # Posortuj węzły według score i usuń nadmiarowe
        sorted_nodes = sorted(node_scores.items(), key=lambda x: x[1])
        to_remove = sorted_nodes[:len(self.nodes) - self.max_nodes]
        
        for node_id, _ in to_remove:
            # Usuń węzeł i jego powiązania
            node = self.nodes.pop(node_id)
            for tag in node.tags:
                if node_id in self.tag_index.get(tag, set()):
                    self.tag_index[tag].remove(node_id)
            
            # Usuń połączenia z innymi węzłami
            for other_id in node.connections:
                if other_id in self.nodes and node_id in self.nodes[other_id].connections:
                    del self.nodes[other_id].connections[node_id]
            
            # Soft delete w bazie danych
            self._soft_delete_from_db(node_id)
    
    def get(self, node_id: str) -> Optional[MemoryNode]:
        """
        Pobiera węzeł po ID
        
        Args:
            node_id: ID węzła
            
        Returns:
            Węzeł lub None jeśli nie znaleziono
        """
        node = self.nodes.get(node_id)
        if node:
            node.access()
        return node
    
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[MemoryNode]:
        """
        Wyszukuje węzły po tagach
        
        Args:
            tags: Lista tagów do wyszukania
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista znalezionych węzłów
        """
        if not tags:
            return []
            
        # Znajdź węzły zawierające dowolny z podanych tagów
        matching_ids = set()
        for tag in tags:
            matching_ids.update(self.tag_index.get(tag, set()))
            
        # Oblicz wynik dla każdego węzła
        results = []
        for node_id in matching_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                node_tags = set(node.tags)
                # Wynik zależy od liczby pasujących tagów i ważności węzła
                matching_tags = [tag for tag in tags if tag in node_tags]
                score = (len(matching_tags) / max(1, len(tags))) * node.importance * node.confidence
                results.append((node, score))
                
        # Posortuj wyniki malejąco według wyniku
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Aktualizuj liczniki dostępu
        nodes = [node for node, _ in results[:limit]]
        for node in nodes:
            node.access()
            
        return nodes
    
    def search_by_text(self, query: str, limit: int = 10) -> List[Tuple[MemoryNode, float]]:
        """
        Wyszukuje węzły po tekście
        
        Args:
            query: Zapytanie
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista krotek (węzeł, wynik)
        """
        # Użyj standardowego wyszukiwania z memory.py
        search_results = _basic_search(query, limit=limit * 2)
        
        # Mapuj wyniki do węzłów w pamięci
        results = []
        for result in search_results:
            node_id = make_id(result["text"])
            if node_id in self.nodes:
                node = self.nodes[node_id]
                node.access()
                results.append((node, float(result["score"])))
        
        return sorted(results, key=lambda x: x[1], reverse=True)[:limit]
    
    def follow_connections(self, node_id: str, min_strength: float = 0.3,
                           limit: int = 5) -> List[Tuple[MemoryNode, float]]:
        """
        Zwraca węzły połączone z danym węzłem
        
        Args:
            node_id: ID węzła źródłowego
            min_strength: Minimalna siła połączenia
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista krotek (węzeł, siła połączenia)
        """
        if node_id not in self.nodes:
            return []
            
        source = self.nodes[node_id]
        results = []
        
        for target_id, strength in source.connections.items():
            if strength >= min_strength and target_id in self.nodes:
                results.append((self.nodes[target_id], strength))
                
        # Posortuj według siły połączenia
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Aktualizuj liczniki dostępu
        for node, _ in results[:limit]:
            node.access()
            
        return results[:limit]
    
    def merge(self, node_id1: str, node_id2: str) -> Optional[str]:
        """
        Łączy dwa węzły w jeden
        
        Args:
            node_id1: ID pierwszego węzła
            node_id2: ID drugiego węzła
            
        Returns:
            ID nowego węzła lub None w przypadku błędu
        """
        if node_id1 not in self.nodes or node_id2 not in self.nodes:
            return None
            
        node1 = self.nodes[node_id1]
        node2 = self.nodes[node_id2]
        
        # Stwórz nowy tekst łączący oba fakty
        merged_text = f"{node1.text} {node2.text}"
        
        # Połącz tagi i usuń duplikaty
        merged_tags = list(set(node1.tags + node2.tags))
        
        # Weź wyższe wartości confidence i importance
        merged_conf = max(node1.confidence, node2.confidence)
        merged_imp = max(node1.importance, node2.importance)
        
        # Stwórz nowy węzeł
        merged_node = MemoryNode(merged_text, merged_tags, merged_conf, merged_imp)
        
        # Połącz wszystkie powiązania
        for conn_id, strength in list(node1.connections.items()) + list(node2.connections.items()):
            if conn_id != node_id1 and conn_id != node_id2:
                merged_node.connections[conn_id] = max(
                    strength,
                    merged_node.connections.get(conn_id, 0.0)
                )
                
        # Usuń stare węzły
        self._remove_node(node_id1)
        self._remove_node(node_id2)
        
        # Dodaj nowy węzeł
        self.nodes[merged_node.id] = merged_node
        
        # Zaktualizuj indeks tagów
        for tag in merged_node.tags:
            self.tag_index[tag].add(merged_node.id)
            
        # Zaktualizuj połączenia w innych węzłach
        for node in self.nodes.values():
            if node_id1 in node.connections or node_id2 in node.connections:
                strength = max(
                    node.connections.get(node_id1, 0.0),
                    node.connections.get(node_id2, 0.0)
                )
                if node_id1 in node.connections:
                    del node.connections[node_id1]
                if node_id2 in node.connections:
                    del node.connections[node_id2]
                node.connections[merged_node.id] = strength
                
        # Zapisz do bazy danych
        self._save_to_db(merged_node)
        self._soft_delete_from_db(node_id1)
        self._soft_delete_from_db(node_id2)
                
        return merged_node.id
    
    def _remove_node(self, node_id: str) -> None:
        """
        Usuwa węzeł z pamięci (bez usuwania z bazy danych)
        
        Args:
            node_id: ID węzła do usunięcia
        """
        if node_id not in self.nodes:
            return
            
        node = self.nodes.pop(node_id)
        
        # Usuń z indeksu tagów
        for tag in node.tags:
            if node_id in self.tag_index.get(tag, set()):
                self.tag_index[tag].remove(node_id)
                
        # Usuń połączenia z innymi węzłami
        for other_id in node.connections:
            if other_id in self.nodes and node_id in self.nodes[other_id].connections:
                del self.nodes[other_id].connections[node_id]
    
    def _save_to_db(self, node: MemoryNode) -> None:
        """
        Zapisuje węzeł do bazy danych
        
        Args:
            node: Węzeł do zapisania
        """
        try:
            # Używamy podstawowej funkcji ltm_add
            _basic_ltm_add(node.text, tags=",".join(node.tags), conf=node.confidence)
        except Exception as e:
            log_error(e, "ASSOC_MEMORY_SAVE")
    
    def _soft_delete_from_db(self, node_id: str) -> None:
        """
        Oznacza węzeł jako usunięty w bazie danych
        
        Args:
            node_id: ID węzła do usunięcia
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE facts SET deleted=1 WHERE id=?", (node_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            log_error(e, "ASSOC_MEMORY_DELETE")
    
    def load_from_db(self, limit: int = None) -> int:
        """
        Ładuje węzły z bazy danych
        
        Args:
            limit: Maksymalna liczba węzłów do załadowania
            
        Returns:
            Liczba załadowanych węzłów
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            query = "SELECT id,text,tags,conf,created FROM facts WHERE deleted=0 ORDER BY created DESC"
            params = []
            
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                
            rows = c.execute(query, params).fetchall()
            conn.close()
            
            # Wyczyść aktualną pamięć
            self.nodes = {}
            self.tag_index = defaultdict(set)
            
            # Załaduj węzły
            for row in rows:
                tags = row["tags"].split(",") if row["tags"] else []
                node = MemoryNode(
                    text=row["text"],
                    tags=tags,
                    confidence=float(row["conf"]),
                    importance=0.5,  # Domyślna wartość
                    created_at=float(row["created"])
                )
                node.id = row["id"]
                self.nodes[node.id] = node
                
                # Zaktualizuj indeks tagów
                for tag in tags:
                    self.tag_index[tag].add(node.id)
                    
            # Utwórz połączenia między węzłami
            for node in list(self.nodes.values()):
                self._create_connections(node)
                
            return len(self.nodes)
        except Exception as e:
            log_error(e, "ASSOC_MEMORY_LOAD")
            return 0
    
    def maintenance(self) -> None:
        """Wykonuje operacje konserwacyjne na pamięci"""
        # Wykonuj nie częściej niż raz na godzinę
        current_time = time.time()
        if current_time - self.last_cleanup < 3600:
            return
            
        self.last_cleanup = current_time
        
        # Osłab nieużywane połączenia
        for node in self.nodes.values():
            node.decay_connections()
            
        # Usuń węzły, jeśli przekroczono limit
        if len(self.nodes) > self.max_nodes:
            self._cleanup_least_important()
            
        log_info(f"Konserwacja pamięci asocjacyjnej zakończona. Aktywnych węzłów: {len(self.nodes)}", "ASSOC_MEM")


# ═══════════════════════════════════════════════════════════════════
# MEMORY CLUSTERING - GRUPOWANIE FAKTÓW
# ═══════════════════════════════════════════════════════════════════

class MemoryClustering:
    """Grupowanie powiązanych faktów w klastry tematyczne"""
    
    def __init__(self, associative_memory: AssociativeMemory):
        """
        Inicjalizuje system grupowania
        
        Args:
            associative_memory: Instancja pamięci asocjacyjnej
        """
        self.memory = associative_memory
        self.clusters = {}  # id klastra -> {node_ids}
        
    async def update_clusters(self) -> Dict[str, Any]:
        """
        Aktualizuje klastry na podstawie aktualnego stanu pamięci
        
        Returns:
            Statystyki operacji
        """
        start_time = time.time()
        
        # Krok 1: Znajdź pary silnie powiązanych węzłów
        strongly_connected = []
        for node_id, node in self.memory.nodes.items():
            for conn_id, strength in node.connections.items():
                if strength >= 0.6 and conn_id in self.memory.nodes:
                    strongly_connected.append((node_id, conn_id, strength))
        
        # Krok 2: Posortuj pary według siły połączenia
        strongly_connected.sort(key=lambda x: x[2], reverse=True)
        
        # Krok 3: Zbuduj klastry
        self.clusters = {}
        node_to_cluster = {}
        
        for node1_id, node2_id, _ in strongly_connected:
            # Jeśli oba węzły mają już klaster
            if node1_id in node_to_cluster and node2_id in node_to_cluster:
                cluster1 = node_to_cluster[node1_id]
                cluster2 = node_to_cluster[node2_id]
                
                # Jeśli różne klastry, połącz je
                if cluster1 != cluster2:
                    self._merge_clusters(cluster1, cluster2)
            # Jeśli tylko jeden węzeł ma klaster
            elif node1_id in node_to_cluster:
                cluster = node_to_cluster[node1_id]
                self.clusters[cluster].add(node2_id)
                node_to_cluster[node2_id] = cluster
            elif node2_id in node_to_cluster:
                cluster = node_to_cluster[node2_id]
                self.clusters[cluster].add(node1_id)
                node_to_cluster[node1_id] = cluster
            # Jeśli żaden węzeł nie ma klastra
            else:
                cluster_id = f"c_{len(self.clusters)}"
                self.clusters[cluster_id] = {node1_id, node2_id}
                node_to_cluster[node1_id] = cluster_id
                node_to_cluster[node2_id] = cluster_id
        
        # Krok 4: Przetwarzanie równoległe - znajdź wspólne tematy dla każdego klastra
        cluster_topics = {}
        
        async def process_cluster(cluster_data):
            cluster_id, node_ids = cluster_data
            # Zbierz wszystkie tagi z węzłów w klastrze
            all_tags = []
            for node_id in node_ids:
                if node_id in self.memory.nodes:
                    node = self.memory.nodes[node_id]
                    all_tags.extend(node.tags)
                    
            # Znajdź najczęstsze tagi
            tag_counts = defaultdict(int)
            for tag in all_tags:
                tag_counts[tag] += 1
                
            # Posortuj według liczby wystąpień
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            top_tags = [tag for tag, _ in sorted_tags[:5]]
            
            return cluster_id, top_tags
        
        # Przetwórz klastry równolegle
        cluster_items = [(cid, nodes) for cid, nodes in self.clusters.items()]
        results = await parallel_map(process_cluster, cluster_items)
        
        for cluster_id, top_tags in results:
            cluster_topics[cluster_id] = top_tags
        
        # Statystyki
        total_time = time.time() - start_time
        stats = {
            "clusters_count": len(self.clusters),
            "avg_cluster_size": sum(len(c) for c in self.clusters.values()) / max(1, len(self.clusters)),
            "largest_cluster": max([len(c) for c in self.clusters.values()], default=0),
            "processing_time": total_time,
            "topics": cluster_topics
        }
        
        log_info(f"Zaktualizowano klastry pamięci. Liczba klastrów: {stats['clusters_count']}", "MEM_CLUSTER")
        
        return stats
    
    def _merge_clusters(self, cluster1_id: str, cluster2_id: str) -> None:
        """
        Łączy dwa klastry
        
        Args:
            cluster1_id: ID pierwszego klastra
            cluster2_id: ID drugiego klastra
        """
        if cluster1_id not in self.clusters or cluster2_id not in self.clusters:
            return
            
        # Dodaj węzły z klastra 2 do klastra 1
        self.clusters[cluster1_id].update(self.clusters[cluster2_id])
        
        # Zaktualizuj mapowanie węzłów
        for node_id in self.clusters[cluster2_id]:
            node_to_cluster = {n: c for n, c in zip(
                [nid for c in self.clusters.values() for nid in c], 
                [cid for cid, nodes in self.clusters.items() for _ in nodes]
            )}
            node_to_cluster[node_id] = cluster1_id
        
        # Usuń klaster 2
        del self.clusters[cluster2_id]
    
    async def get_cluster_summary(self, cluster_id: str, max_length: int = 500) -> Optional[str]:
        """
        Generuje podsumowanie klastra
        
        Args:
            cluster_id: ID klastra
            max_length: Maksymalna długość podsumowania
            
        Returns:
            Podsumowanie klastra lub None jeśli nie znaleziono
        """
        if cluster_id not in self.clusters:
            return None
            
        # Zbierz teksty faktów z klastra
        facts = []
        for node_id in self.clusters[cluster_id]:
            if node_id in self.memory.nodes:
                facts.append(self.memory.nodes[node_id].text)
                
        if not facts:
            return None
            
        # Użyj LLM do wygenerowania podsumowania
        from .llm import _llm_request
        
        prompt = f"""Wygeneruj zwięzłe podsumowanie poniższych powiązanych faktów:

{', '.join(facts[:10])}

Podsumowanie (maksymalnie 3 zdania):"""
        
        try:
            summary = await task_pool.submit(
                _llm_request, 
                messages=[
                    {"role": "system", "content": "Jesteś pomocnym asystentem specjalizującym się w tworzeniu zwięzłych podsumowań."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=150
            )
            
            # Ogranicz długość
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
                
            return summary
        except Exception as e:
            log_error(e, "CLUSTER_SUMMARY")
            
            # Fallback - proste podsumowanie
            all_text = " ".join(facts)
            if len(all_text) > max_length:
                return all_text[:max_length-3] + "..."
            return all_text


# ═══════════════════════════════════════════════════════════════════
# ADVANCED MEMORY OPERATIONS
# ═══════════════════════════════════════════════════════════════════

# Globalne instancje pamięci
associative_memory = AssociativeMemory()
memory_clustering = MemoryClustering(associative_memory)


async def initialize_memory() -> None:
    """Inicjalizuje zaawansowane struktury pamięci"""
    log_info("Inicjalizacja zaawansowanych struktur pamięci...", "ADV_MEM")
    
    # Załaduj fakty z bazy danych do pamięci asocjacyjnej
    loaded = associative_memory.load_from_db(limit=LTM_CACHE_SIZE)
    log_info(f"Załadowano {loaded} faktów do pamięci asocjacyjnej", "ADV_MEM")
    
    # Zaktualizuj klastry pamięci
    if loaded > 0:
        await memory_clustering.update_clusters()
    
    log_info("Inicjalizacja zaawansowanych struktur pamięci zakończona", "ADV_MEM")


async def ltm_add_with_connections(text: str, tags: str = "", conf: float = 0.7,
                                  related_texts: List[str] = None) -> Dict[str, Any]:
    """
    Dodaje fakt do pamięci długoterminowej z automatycznym tworzeniem połączeń
    
    Args:
        text: Treść faktu
        tags: Tagi oddzielone przecinkami
        conf: Pewność faktu (0-1)
        related_texts: Lista powiązanych tekstów
        
    Returns:
        Słownik z informacjami o dodanym fakcie
    """
    # Konwersja tagów na listę
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    # Dodaj fakt do pamięci asocjacyjnej
    node_id = associative_memory.add(text, tag_list, conf)
    
    # Dodaj połączenia z powiązanymi tekstami
    if related_texts:
        for related_text in related_texts:
            related_id = make_id(related_text)
            if related_id in associative_memory.nodes and related_id != node_id:
                associative_memory.nodes[node_id].connect(related_id, 0.7)
                associative_memory.nodes[related_id].connect(node_id, 0.7)
    
    # Wykonaj konserwację pamięci (jeśli potrzebna)
    associative_memory.maintenance()
    
    return {
        "id": node_id,
        "text": text,
        "tags": tag_list,
        "confidence": conf
    }


async def ltm_search_enhanced(query: str, limit: int = 10, 
                             follow_connections: bool = True) -> List[Dict[str, Any]]:
    """
    Rozszerzone wyszukiwanie w pamięci długoterminowej
    
    Args:
        query: Zapytanie
        limit: Maksymalna liczba wyników
        follow_connections: Czy podążać za połączeniami
        
    Returns:
        Lista wyników
    """
    # Wyszukaj węzły po tekście
    text_results = associative_memory.search_by_text(query, limit=limit)
    
    # Jeśli mamy wyniki i podążamy za połączeniami
    connected_results = []
    if text_results and follow_connections:
        # Znajdź połączone węzły dla pierwszego wyniku
        first_node, first_score = text_results[0]
        connections = associative_memory.follow_connections(
            first_node.id, min_strength=0.5, limit=limit // 2
        )
        connected_results = [(node, score * 0.8) for node, score in connections]
    
    # Połącz wyniki
    all_results = text_results + connected_results
    
    # Usuń duplikaty i posortuj
    seen_ids = set()
    unique_results = []
    
    for node, score in all_results:
        if node.id not in seen_ids:
            seen_ids.add(node.id)
            unique_results.append((node, score))
    
    # Posortuj malejąco według wyniku
    unique_results.sort(key=lambda x: x[1], reverse=True)
    
    # Konwertuj do formatu wyjściowego
    output = []
    for node, score in unique_results[:limit]:
        output.append({
            "id": node.id,
            "text": node.text,
            "tags": node.tags,
            "confidence": node.confidence,
            "score": float(score)
        })
    
    return output


async def get_related_memories(text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Znajduje wspomnienia powiązane z podanym tekstem
    
    Args:
        text: Tekst do znalezienia powiązanych wspomnień
        limit: Maksymalna liczba wyników
        
    Returns:
        Lista powiązanych wspomnień
    """
    # Wyszukaj węzły po tekście
    text_results = associative_memory.search_by_text(text, limit=2)
    
    if not text_results:
        return []
    
    # Weź pierwszy węzeł i znajdź jego połączenia
    first_node, _ = text_results[0]
    connections = associative_memory.follow_connections(
        first_node.id, min_strength=0.3, limit=limit
    )
    
    # Konwertuj do formatu wyjściowego
    results = []
    for node, strength in connections:
        results.append({
            "id": node.id,
            "text": node.text,
            "tags": node.tags,
            "confidence": node.confidence,
            "connection_strength": float(strength),
            "relevance": "high" if strength >= 0.7 else "medium" if strength >= 0.5 else "low"
        })
    
    return results


async def get_memory_clusters(limit: int = 3) -> List[Dict[str, Any]]:
    """
    Zwraca najważniejsze klastry pamięci
    
    Args:
        limit: Maksymalna liczba klastrów
        
    Returns:
        Lista klastrów
    """
    # Upewnij się, że klastry są zaktualizowane
    await memory_clustering.update_clusters()
    
    # Posortuj klastry według rozmiaru
    sorted_clusters = sorted(
        memory_clustering.clusters.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    # Przygotuj wyniki
    results = []
    for cluster_id, node_ids in sorted_clusters[:limit]:
        # Pobierz podsumowanie klastra
        summary = await memory_clustering.get_cluster_summary(cluster_id)
        
        # Zbierz najważniejsze fakty z klastra
        facts = []
        for node_id in list(node_ids)[:5]:  # Maks. 5 faktów na klaster
            if node_id in associative_memory.nodes:
                node = associative_memory.nodes[node_id]
                facts.append({
                    "id": node.id,
                    "text": node.text,
                    "tags": node.tags,
                    "importance": node.importance
                })
        
        results.append({
            "id": cluster_id,
            "size": len(node_ids),
            "summary": summary,
            "top_facts": facts
        })
    
    return results