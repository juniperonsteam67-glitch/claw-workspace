#!/usr/bin/env python3
"""
claw_autolearn.py - Autonomous Learning System for OpenClaw

Proactively researches topics and builds knowledge without being asked.
Can run periodically via cron or on-demand via CLI.

Usage:
    autolearn                 # Run learning cycle on random topic
    autolearn --topic "AI"    # Learn about specific topic  
    autolearn --list          # Show learned topics
    autolearn --status        # Show learning statistics
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import urllib.request
import urllib.error
import time

# Configuration
MEMORY_DIR = Path("/config/clawd/memory")
LEARNED_DIR = MEMORY_DIR / "learned_knowledge"
LEARNED_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = LEARNED_DIR / "autolearn_state.json"
TOPICS_FILE = LEARNED_DIR / "topic_queue.json"

def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable, checking multiple sources."""
    # Check .env file
    env_file = Path("/config/clawd/.env")
    if env_file.exists():
        content = env_file.read_text()
        for line in content.split('\n'):
            if line.startswith(f"{key}="):
                return line.split('=', 1)[1].strip().strip('"\'')
    return os.environ.get(key, default)

# Curated topic list - seeded from capabilities, tools, interests
DEFAULT_TOPICS = [
    # AI & Machine Learning
    "large language models architecture",
    "transformer neural networks explained",
    "AI agent frameworks 2025",
    "prompt engineering techniques",
    "RAG retrieval augmented generation",
    "vector databases comparison",
    "local LLM deployment strategies",
    "AI safety and alignment",
    "multimodal AI models",
    "reinforcement learning from human feedback",
    
    # Programming & Software Engineering  
    "Python async await patterns",
    "Rust memory safety features",
    "Go concurrency patterns",
    "TypeScript advanced types",
    "system design patterns",
    "microservices architecture",
    "event-driven architecture",
    "domain driven design principles",
    "test-driven development best practices",
    "continuous deployment strategies",
    "observability and monitoring",
    "distributed tracing",
    "API design best practices",
    "graphQL vs REST APIs",
    "WebSocket real-time communication",
    
    # DevOps & Infrastructure
    "Docker container optimization",
    "Kubernetes deployment patterns", 
    "GitHub Actions CI/CD workflows",
    "infrastructure as code Terraform",
    "home automation best practices",
    "Home Assistant automation tips",
    "network monitoring tools",
    "Linux performance tuning",
    "shell scripting best practices",
    "systemd service management",
    "nginx reverse proxy configuration",
    "SSL certificate management",
    "backup strategies 3-2-1 rule",
    
    # Data & Databases
    "PostgreSQL performance optimization",
    "Redis caching strategies",
    "time series databases",
    "data pipeline architecture",
    "ETL vs ELT data processing",
    "data validation techniques",
    
    # Security
    "zero trust security model",
    "OAuth 2.0 and OpenID Connect",
    "secrets management best practices",
    "supply chain security",
    "secure coding practices",
    
    # Web & Frontend
    "React server components",
    "Next.js app router features",
    "CSS container queries",
    "web accessibility WCAG guidelines",
    "progressive web apps",
    "web performance optimization",
    
    # Emerging Tech
    "WebAssembly use cases",
    "edge computing platforms",
    "WebRTC video streaming",
    "IoT device security",
    "blockchain beyond cryptocurrency",
    "quantum computing basics",
    
    # Productivity & Tools
    "VS Code extensions productivity",
    "terminal productivity tools",
    "git advanced workflows",
    "documentation as code",
    "markdown best practices",
    
    # Philosophy of Technology
    "human AI collaboration",
    "digital minimalism",
    "privacy vs convenience",
    "open source sustainability",
    "tech ethics considerations",
]

class AutoLearner:
    """Autonomous learning system that researches and stores knowledge."""
    
    def __init__(self):
        self.state = self._load_state()
        self.topics_queue = self._load_topics_queue()
        
    def _load_state(self) -> dict:
        """Load or initialize the learning state."""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "learned_topics": [],
            "total_articles_read": 0,
            "last_run": None,
            "session_count": 0,
            "started_at": datetime.now().isoformat()
        }
    
    def _save_state(self):
        """Save the learning state."""
        STATE_FILE.write_text(json.dumps(self.state, indent=2))
    
    def _load_topics_queue(self) -> dict:
        """Load or initialize the topic queue."""
        if TOPICS_FILE.exists():
            try:
                return json.loads(TOPICS_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "available": DEFAULT_TOPICS.copy(),
            "custom": [],
            "exhausted": []
        }
    
    def _save_topics_queue(self):
        """Save the topic queue."""
        TOPICS_FILE.write_text(json.dumps(self.topics_queue, indent=2))
    
    def _generate_topic_id(self, topic: str) -> str:
        """Generate a unique ID for a topic."""
        return hashlib.md5(topic.lower().encode()).hexdigest()[:12]
    
    def _is_topic_learned(self, topic: str) -> bool:
        """Check if a topic has already been learned."""
        topic_id = self._generate_topic_id(topic)
        return any(t.get("id") == topic_id for t in self.state["learned_topics"])
    
    def _search_web(self, query: str, count: int = 5) -> list[dict]:
        """Search the web using Brave API via web_search tool."""
        # Check for API key
        api_key = get_env_var("BRAVE_API_KEY")
        if not api_key:
            print("⚠️  BRAVE_API_KEY not found. Using fallback search method.")
            return self._fallback_search(query, count)
        
        try:
            # Call web_search via subprocess (simulating tool usage)
            import subprocess
            result = subprocess.run(
                ["python3", "-c", f"""
import json
import sys
sys.path.insert(0, '/config/clawd/tools')
from claw_autolearn import web_search_tool
results = web_search_tool("{query}", {count})
print(json.dumps(results))
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Search error: {e}")
        
        return self._fallback_search(query, count)
    
    def _fallback_search(self, query: str, count: int = 5) -> list[dict]:
        """Fallback search using basic web knowledge."""
        # Return empty - will use placeholder content
        return []
    
    def _fetch_article(self, url: str) -> str:
        """Fetch and extract content from a URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8', errors='ignore')
                return self._extract_text_from_html(html)
        except Exception as e:
            print(f"  ⚠️  Failed to fetch {url}: {e}")
            return ""
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract readable text from HTML."""
        # Simple HTML tag removal
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()[:15000]  # Limit content length
    
    def _extract_insights(self, content: str, topic: str) -> list[str]:
        """Extract key insights from article content."""
        insights = []
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # Look for definition/explanation patterns
        topic_words = topic.lower().split()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30 or len(sentence) > 300:
                continue
            
            # Score the sentence for insight value
            score = 0
            s_lower = sentence.lower()
            
            # Contains topic words
            if any(word in s_lower for word in topic_words if len(word) > 3):
                score += 2
            
            # Contains definition patterns
            if any(pattern in s_lower for pattern in ['is a', 'refers to', 'defined as', 'means', 'describes']):
                score += 3
            
            # Contains list/sequence patterns  
            if any(pattern in s_lower for pattern in ['first', 'second', 'third', 'steps', 'process', 'method']):
                score += 1
            
            # Contains comparison
            if any(pattern in s_lower for pattern in ['compared to', 'versus', 'difference', 'similar', 'unlike']):
                score += 2
            
            # Contains advice/best practice
            if any(pattern in s_lower for pattern in ['best practice', 'recommend', 'should', 'important', 'key', 'essential']):
                score += 2
                
            if score >= 4:
                insights.append(sentence)
        
        # Return top insights, deduplicated
        seen = set()
        unique_insights = []
        for insight in insights[:15]:
            key = insight[:50].lower()
            if key not in seen:
                seen.add(key)
                unique_insights.append(insight)
        
        return unique_insights[:10]
    
    def _synthesize_knowledge(self, topic: str, articles: list[dict], all_insights: list[list[str]]) -> dict:
        """Synthesize knowledge from multiple sources."""
        # Flatten and deduplicate insights
        all_flat = []
        for insights in all_insights:
            all_flat.extend(insights)
        
        # Group by theme
        themes = {
            "definitions": [],
            "concepts": [],
            "practices": [],
            "tools": [],
            "considerations": []
        }
        
        for insight in all_flat:
            il = insight.lower()
            if any(w in il for w in ['is a', 'refers to', 'defined as']):
                themes["definitions"].append(insight)
            elif any(w in il for w in ['should', 'recommend', 'best practice', 'avoid']):
                themes["practices"].append(insight)
            elif any(w in il for w in ['tool', 'framework', 'library', 'platform']):
                themes["tools"].append(insight)
            elif any(w in il for w in ['important', 'consider', 'note that', 'key']):
                themes["considerations"].append(insight)
            else:
                themes["concepts"].append(insight)
        
        # Build summary
        summary_points = []
        if themes["definitions"]:
            summary_points.append(f"{topic} refers to a field/concept involving {themes['definitions'][0][:100]}...")
        if themes["concepts"]:
            summary_points.append(f"Key concepts include: {themes['concepts'][0][:100]}...")
        
        return {
            "summary": " ".join(summary_points) if summary_points else f"Research on {topic}",
            "themes": {k: v[:5] for k, v in themes.items() if v},
            "sources": [{"title": a.get("title", ""), "url": a.get("url", "")} for a in articles]
        }
    
    def _store_knowledge(self, topic: str, knowledge: dict, articles_read: int):
        """Store the learned knowledge to file."""
        topic_id = self._generate_topic_id(topic)
        timestamp = datetime.now().isoformat()
        
        knowledge_file = LEARNED_DIR / f"{topic_id}.json"
        
        knowledge_data = {
            "id": topic_id,
            "topic": topic,
            "learned_at": timestamp,
            "knowledge": knowledge,
            "articles_read": articles_read,
            "version": "1.0"
        }
        
        knowledge_file.write_text(json.dumps(knowledge_data, indent=2))
        
        # Update state
        self.state["learned_topics"].append({
            "id": topic_id,
            "topic": topic,
            "learned_at": timestamp,
            "articles_read": articles_read
        })
        self.state["total_articles_read"] += articles_read
        self.state["last_run"] = timestamp
        self.state["session_count"] += 1
        self._save_state()
        
        return knowledge_file
    
    def learn_topic(self, topic: str = None, force: bool = False) -> dict:
        """Learn about a specific topic or pick one randomly."""
        # Select topic
        if topic:
            print(f"📚 Learning about: {topic}")
        else:
            # Pick from available topics
            available = [t for t in self.topics_queue["available"] 
                        if not self._is_topic_learned(t)]
            
            if not available:
                # Reset exhausted topics
                print("🔄 All topics learned! Resetting queue...")
                self.topics_queue["available"] = DEFAULT_TOPICS.copy()
                self.topics_queue["exhausted"] = []
                available = self.topics_queue["available"]
            
            topic = random.choice(available)
            print(f"📚 Randomly selected topic: {topic}")
        
        # Check for duplicates
        if self._is_topic_learned(topic) and not force:
            print(f"⚠️  Already learned about '{topic}'. Use --force to relearn.")
            return None
        
        print(f"🔍 Searching for information...")
        
        # Search for articles
        search_results = self._search_web(topic, count=5)
        
        if not search_results:
            print("⚠️  No search results found. Using placeholder learning.")
            search_results = [
                {"title": f"Understanding {topic}", "url": "https://example.com/placeholder", "snippet": f"A guide to understanding {topic} and its applications."},
                {"title": f"{topic.title()} Best Practices", "url": "https://example.com/best-practices", "snippet": f"Best practices for working with {topic}."}
            ]
        
        print(f"📖 Found {len(search_results)} sources")
        
        # Fetch and process articles
        all_insights = []
        articles_processed = 0
        
        for i, result in enumerate(search_results[:3], 1):
            url = result.get("url", "")
            title = result.get("title", "Unknown")
            
            if not url or url == "https://example.com/placeholder":
                # Use snippet as content for placeholder
                content = result.get("snippet", "")
                if content:
                    insights = self._extract_insights(content, topic)
                    if insights:
                        all_insights.append(insights)
                        articles_processed += 1
                continue
            
            print(f"  📄 Reading: {title[:60]}...")
            content = self._fetch_article(url)
            
            if content:
                insights = self._extract_insights(content, topic)
                if insights:
                    all_insights.append(insights)
                    articles_processed += 1
                    print(f"     ✓ Extracted {len(insights)} insights")
                else:
                    print(f"     ⚠️  No insights extracted")
            
            # Small delay to be respectful
            time.sleep(0.5)
        
        # Synthesize knowledge
        print("🧠 Synthesizing knowledge...")
        knowledge = self._synthesize_knowledge(topic, search_results, all_insights)
        
        # Store knowledge
        knowledge_file = self._store_knowledge(topic, knowledge, articles_processed)
        
        print(f"\n✅ Learning complete!")
        print(f"   Topic: {topic}")
        print(f"   Articles processed: {articles_processed}")
        print(f"   Insights extracted: {sum(len(i) for i in all_insights)}")
        print(f"   Stored in: {knowledge_file}")
        
        return {
            "topic": topic,
            "file": str(knowledge_file),
            "articles_read": articles_processed,
            "insights_count": sum(len(i) for i in all_insights)
        }
    
    def list_learned(self) -> list[dict]:
        """List all learned topics."""
        return self.state.get("learned_topics", [])
    
    def get_status(self) -> dict:
        """Get learning system status."""
        return {
            "total_topics_learned": len(self.state.get("learned_topics", [])),
            "total_articles_read": self.state.get("total_articles_read", 0),
            "sessions_completed": self.state.get("session_count", 0),
            "started_at": self.state.get("started_at"),
            "last_run": self.state.get("last_run"),
            "available_topics": len(self.topics_queue.get("available", [])),
            "storage_location": str(LEARNED_DIR)
        }
    
    def read_knowledge(self, topic_id: str = None, topic_name: str = None) -> dict:
        """Read stored knowledge for a topic."""
        if topic_id:
            file_path = LEARNED_DIR / f"{topic_id}.json"
            if file_path.exists():
                return json.loads(file_path.read_text())
        
        if topic_name:
            # Search by name
            search_lower = topic_name.lower()
            for learned in self.state.get("learned_topics", []):
                if search_lower in learned.get("topic", "").lower():
                    file_path = LEARNED_DIR / f"{learned['id']}.json"
                    if file_path.exists():
                        return json.loads(file_path.read_text())
        
        return None


def web_search_tool(query: str, count: int = 5) -> list[dict]:
    """Standalone web search function that can be called as a tool."""
    api_key = get_env_var("BRAVE_API_KEY")
    
    if not api_key:
        return []
    
    try:
        import urllib.request
        import urllib.parse
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.search.brave.com/res/v1/web/search?q={encoded_query}&count={count}"
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            results = []
            for item in data.get("web", {}).get("results", [])[:count]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", "")
                })
            return results
            
    except Exception as e:
        print(f"Search error: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Learning System - Learn without being asked",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  autolearn                  # Learn about a random topic
  autolearn --topic "AI"     # Learn about specific topic
  autolearn --list           # List all learned topics
  autolearn --status         # Show system status
  autolearn --read python    # Read knowledge about python
        """
    )
    
    parser.add_argument("--topic", "-t", 
                       help="Specific topic to learn about")
    parser.add_argument("--list", "-l", 
                       action="store_true",
                       help="List all learned topics")
    parser.add_argument("--status", "-s", 
                       action="store_true", 
                       help="Show learning system status")
    parser.add_argument("--read", "-r",
                       metavar="TOPIC",
                       help="Read knowledge about a specific topic")
    parser.add_argument("--force", "-f",
                       action="store_true",
                       help="Force relearning of already-learned topic")
    parser.add_argument("--count", "-c",
                       type=int, 
                       default=5,
                       help="Number of search results to fetch (default: 5)")
    
    args = parser.parse_args()
    
    learner = AutoLearner()
    
    if args.list:
        learned = learner.list_learned()
        if not learned:
            print("📭 No topics learned yet.")
            print(f"   Run 'autolearn' to start learning!")
        else:
            print(f"📚 Learned Topics ({len(learned)} total):\n")
            for item in learned[-20:]:  # Show last 20
                topic = item.get("topic", "Unknown")
                when = item.get("learned_at", "Unknown")[:10]
                articles = item.get("articles_read", 0)
                print(f"  • {topic[:50]:<50} ({when}, {articles} articles)")
            if len(learned) > 20:
                print(f"\n  ... and {len(learned) - 20} more")
        return
    
    if args.status:
        status = learner.get_status()
        print("🧠 Autonomous Learning System Status\n")
        print(f"  Topics learned:     {status['total_topics_learned']}")
        print(f"  Articles processed: {status['total_articles_read']}")
        print(f"  Learning sessions:  {status['sessions_completed']}")
        print(f"  Started:            {status['started_at'][:10] if status['started_at'] else 'Never'}")
        print(f"  Last run:           {status['last_run'][:10] if status['last_run'] else 'Never'}")
        print(f"  Available topics:   {status['available_topics']}")
        print(f"  Storage:            {status['storage_location']}")
        return
    
    if args.read:
        knowledge = learner.read_knowledge(topic_name=args.read)
        if knowledge:
            print(f"📖 Knowledge: {knowledge['topic']}\n")
            print(f"Learned: {knowledge['learned_at'][:10]}")
            print(f"Articles: {knowledge['articles_read']}\n")
            
            k = knowledge.get("knowledge", {})
            if "summary" in k:
                print(f"Summary:\n  {k['summary']}\n")
            
            themes = k.get("themes", {})
            for theme_name, insights in themes.items():
                if insights:
                    print(f"{theme_name.title()}:")
                    for insight in insights[:3]:
                        print(f"  • {insight[:150]}...")
                    print()
        else:
            print(f"❌ No knowledge found for '{args.read}'")
            print(f"   Run 'autolearn --topic \"{args.read}\"' to learn about it!")
        return
    
    # Default: learn a topic
    result = learner.learn_topic(topic=args.topic, force=args.force)
    
    if result:
        print(f"\n💡 Tip: Run 'autolearn --read \"{result['topic'][:30]}\"' to review this knowledge")


if __name__ == "__main__":
    main()
