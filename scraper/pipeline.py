"""
Streaming ingestion pipeline.
Fetches from multiple sources concurrently, deduplicates with MinHash,
and writes structured records to SQLite.
BAX-423 Technique: Streaming (producer/consumer pattern with threading).
"""
import threading
import queue
import time
import logging
from datetime import datetime
from db.database import get_connection, init_db, insert_opportunity, count_opportunities
from scraper.minhash_dedup import MinHashDeduplicator

logger = logging.getLogger(__name__)


class StreamingPipeline:
    def __init__(self, db_path: str = None, queue_size: int = 2000):
        self.db_path = db_path
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        self._dedup = MinHashDeduplicator()
        self._stop_event = threading.Event()
        self._stats = {"ingested": 0, "duplicates": 0, "errors": 0}
        self._lock = threading.Lock()

    def _producer_github(self, target_per_domain: int = 60):
        from scraper.github_scraper import scrape_all_domains
        try:
            items = scrape_all_domains(target_per_domain)
            for item in items:
                if not self._stop_event.is_set():
                    self._queue.put(item, timeout=5)
        except Exception as e:
            logger.error(f"GitHub producer error: {e}")

    def _producer_hackernews(self, limit: int = 800):
        from scraper.hackernews_scraper import scrape_all
        try:
            items = scrape_all(limit)
            for item in items:
                if not self._stop_event.is_set():
                    self._queue.put(item, timeout=5)
        except Exception as e:
            logger.error(f"HN producer error: {e}")

    def _consumer(self):
        conn = get_connection(self.db_path)
        while not (self._stop_event.is_set() and self._queue.empty()):
            try:
                item = self._queue.get(timeout=2)
                text = f"{item.get('title', '')} {item.get('body', '')}"
                is_dup, sig = self._dedup.check_and_add(text)
                if is_dup:
                    with self._lock:
                        self._stats["duplicates"] += 1
                    self._queue.task_done()
                    continue
                item["minhash"] = sig[:20]
                result = insert_opportunity(conn, item)
                with self._lock:
                    if result:
                        self._stats["ingested"] += 1
                    else:
                        self._stats["duplicates"] += 1
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                with self._lock:
                    self._stats["errors"] += 1
                try:
                    self._queue.task_done()
                except Exception:
                    pass
        conn.close()

    def run(self, progress_callback=None) -> dict:
        init_db(self.db_path)
        threads = [
            threading.Thread(target=self._producer_github, args=(60,), daemon=True),
            threading.Thread(target=self._producer_hackernews, args=(600,), daemon=True),
            threading.Thread(target=self._consumer, daemon=True),
        ]
        for t in threads:
            t.start()

        producers = threads[:2]
        consumer = threads[2]

        for t in producers:
            t.join()

        self._stop_event.set()
        consumer.join(timeout=30)

        conn = get_connection(self.db_path)
        total = count_opportunities(conn)
        conn.close()
        self._stats["total_in_db"] = total
        return self._stats

    @property
    def stats(self) -> dict:
        return dict(self._stats)


def run_live_refresh(db_path: str = None, progress_callback=None) -> dict:
    """Entry point for the live refresh button in the Streamlit UI."""
    pipeline = StreamingPipeline(db_path=db_path)
    return pipeline.run(progress_callback=progress_callback)
