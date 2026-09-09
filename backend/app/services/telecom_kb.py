import os
import json
import re
from typing import List, Dict, Any, Optional
from app.config import config

KB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "telecom_kb.json"))

class TelecomKnowledgeService:
    """
    Telecom Domain Knowledge Base and Ingestion Service (Defect-2).
    Provides instant deterministic matching for telco inquiries (eSIM, Roaming,
    Wi-Fi passwords, Router status lights, MNP porting, Relocation, APN settings).
    Supports dynamic ingestion via Admin UI, REST API, or JSON file.
    """

    def __init__(self):
        self._articles: List[Dict[str, Any]] = []
        self.load_knowledge_base()

    def load_knowledge_base(self):
        if os.path.exists(KB_FILE):
            try:
                with open(KB_FILE, "r", encoding="utf-8") as f:
                    self._articles = json.load(f)
            except Exception as e:
                print(f"[TelecomKnowledgeService] Error loading KB file: {e}")
                self._articles = []
        else:
            self._articles = []

    def save_knowledge_base(self):
        os.makedirs(os.path.dirname(KB_FILE), exist_ok=True)
        with open(KB_FILE, "w", encoding="utf-8") as f:
            json.dump(self._articles, f, indent=2, ensure_ascii=False)

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._articles)

    def get_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        for art in self._articles:
            if art.get("id") == article_id:
                return art
        return None

    def upsert_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates or updates a knowledge article and writes to storage.
        """
        art_id = article_data.get("id")
        if not art_id:
            topic_slug = re.sub(r'[^a-zA-Z0-9]+', '_', article_data.get("topic", "kb").lower()).strip('_')
            art_id = f"kb_{topic_slug}_{len(self._articles)+1}"
            article_data["id"] = art_id

        # Replace existing or append new
        found = False
        for i, existing in enumerate(self._articles):
            if existing.get("id") == art_id:
                self._articles[i] = article_data
                found = True
                break

        if not found:
            self._articles.append(article_data)

        self.save_knowledge_base()
        return article_data

    def delete_article(self, article_id: str) -> bool:
        initial_len = len(self._articles)
        self._articles = [a for a in self._articles if a.get("id") != article_id]
        if len(self._articles) < initial_len:
            self.save_knowledge_base()
            return True
        return False

    def import_batch(self, items: List[Dict[str, Any]]) -> int:
        count = 0
        for item in items:
            if isinstance(item, dict) and "topic" in item and "answers" in item:
                self.upsert_article(item)
                count += 1
        return count

    def find_match(self, query: str, language: str = "en-US") -> Optional[Dict[str, Any]]:
        """
        Scans all articles to find best match for user query.
        Returns match dict with answer in requested language or None if under confidence threshold.
        """
        if not query or not self._articles:
            return None

        lowered = query.lower().strip()
        cleaned = re.sub(r"[^\w\s]", " ", lowered)
        words = set(cleaned.split())

        best_article = None
        best_score = 0.0

        lang_key = "es" if language.startswith("es") else ("hi" if language.startswith("hi") else "en")

        for article in self._articles:
            keywords = [k.lower() for k in article.get("keywords", [])]
            questions = [q.lower() for q in article.get("questions", [])]
            topic = article.get("topic", "").lower()

            score = 0.0

            # 1. Exact phrase in keywords
            for kw in keywords:
                if kw in lowered:
                    # Multi-word keyword matches get higher weight
                    kw_len = len(kw.split())
                    match_score = 0.85 + min(0.10, kw_len * 0.03)
                    if match_score > score:
                        score = match_score

            # 2. Word overlap against keywords
            kw_tokens = set(" ".join(keywords).split())
            common_tokens = words.intersection(kw_tokens)
            if common_tokens:
                overlap_score = 0.50 + (len(common_tokens) / max(len(words), 1)) * 0.40
                if overlap_score > score:
                    score = overlap_score

            # 3. Check sample questions
            for q in questions:
                if q in lowered or lowered in q:
                    if 0.92 > score:
                        score = 0.92

            if score > best_score:
                best_score = score
                best_article = article

        # Confidence threshold: 0.70
        if best_article and best_score >= 0.70:
            answers = best_article.get("answers", {})
            answer_text = answers.get(lang_key) or answers.get("en") or "I have information regarding that topic. Please let me know how else I can assist."
            return {
                "article_id": best_article.get("id"),
                "topic": best_article.get("topic"),
                "category": best_article.get("category"),
                "answer": answer_text,
                "confidence": round(best_score, 2)
            }

        return None

telecom_kb_service = TelecomKnowledgeService()
