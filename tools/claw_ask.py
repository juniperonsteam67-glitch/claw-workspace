#!/usr/bin/env python3
"""
claw_ask.py - Query learned documentation with semantic similarity search

Usage:
    claw_ask "how do I spawn a subagent with a timeout?"
    claw_ask "what are the session tool commands?"
    claw_ask "explain multi-agent routing"
"""

import json
import os
import re
import sys
import math
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple, Optional

# Configuration
LEARNED_DOCS_DIR = Path("/config/clawd/memory/learned_docs")
TOP_K_RESULTS = 5
MIN_SIMILARITY = 0.05


class SemanticSearcher:
    """Simple TF-IDF based semantic similarity searcher."""
    
    def __init__(self):
        self.documents: List[Dict] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization with normalization."""
        text = text.lower()
        # Keep alphanumeric and some technical characters
        text = re.sub(r'[^\w\s\-_\.]', ' ', text)
        tokens = text.split()
        # Simple stemming/prefix matching for technical terms
        filtered = []
        for t in tokens:
            if len(t) > 1 and not t.isdigit():
                filtered.append(t)
        return filtered
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequencies."""
        counts = Counter(tokens)
        total = len(tokens) or 1
        return {term: count / total for term, count in counts.items()}
    
    def _build_vocab(self, all_tokens: List[List[str]]):
        """Build vocabulary and IDF scores."""
        # Count document frequency for each term
        doc_freq = Counter()
        for tokens in all_tokens:
            unique_terms = set(tokens)
            for term in unique_terms:
                doc_freq[term] += 1
        
        n_docs = len(all_tokens) or 1
        self.idf = {
            term: math.log(n_docs / (freq + 1)) + 1
            for term, freq in doc_freq.items()
        }
        self.vocab = {term: i for i, term in enumerate(self.idf.keys())}
    
    def _vectorize(self, tf: Dict[str, float]) -> Dict[str, float]:
        """Create TF-IDF weighted vector."""
        return {term: weight * self.idf.get(term, 1.0) for term, weight in tf.items()}
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Compute cosine similarity between two sparse vectors."""
        dot_product = 0.0
        norm1 = 0.0
        norm2 = 0.0
        
        # Calculate dot product and norms
        all_terms = set(vec1.keys()) | set(vec2.keys())
        for term in all_terms:
            v1 = vec1.get(term, 0.0)
            v2 = vec2.get(term, 0.0)
            dot_product += v1 * v2
            norm1 += v1 * v1
            norm2 += v2 * v2
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (math.sqrt(norm1) * math.sqrt(norm2))
    
    def add_document(self, doc_id: str, title: str, content: str, source: str, 
                     section_name: Optional[str] = None, metadata: Dict = None):
        """Add a document section to the index."""
        tokens = self._tokenize(content)
        self.documents.append({
            'id': doc_id,
            'title': title,
            'content': content,
            'source': source,
            'section': section_name,
            'metadata': metadata or {},
            'tokens': tokens
        })
    
    def build_index(self):
        """Build the search index."""
        all_tokens = [doc['tokens'] for doc in self.documents]
        self._build_vocab(all_tokens)
        
        # Compute TF-IDF vectors for all documents
        self.doc_vectors = []
        for doc in self.documents:
            tf = self._compute_tf(doc['tokens'])
            vector = self._vectorize(tf)
            self.doc_vectors.append(vector)
    
    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Tuple[Dict, float]]:
        """Search for documents semantically similar to the query."""
        query_tokens = self._tokenize(query)
        query_tf = self._compute_tf(query_tokens)
        query_vector = self._vectorize(query_tf)
        
        # Extract key query terms for boosting
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        # Remove common stop words
        stop_words = {'how', 'do', 'i', 'what', 'are', 'the', 'to', 'a', 'an', 'is', 'it', 'with', 'explain'}
        key_terms = query_terms - stop_words
        
        # Score all documents
        scores = []
        for i, doc_vector in enumerate(self.doc_vectors):
            sim = self._cosine_similarity(query_vector, doc_vector)
            doc = self.documents[i]
            title_lower = doc['title'].lower()
            section_lower = (doc.get('section') or '').lower()
            content_lower = doc.get('content', '').lower()[:500]  # Check first part of content
            
            # Boost for key term matches in section names (strong signal)
            for term in key_terms:
                if term in section_lower:
                    sim *= 1.5
                    break
            
            # Boost for key term matches in title
            for term in key_terms:
                if term in title_lower:
                    sim *= 1.3
                    break
            
            # Boost for description/overview sections when query is general
            if 'description' in section_lower or 'overview' in section_lower:
                sim *= 1.15
            
            # Small boost for code examples when query mentions "example" or "how"
            if 'code' in section_lower and ('example' in query_lower or 'how' in query_lower):
                sim *= 1.1
            
            if sim >= MIN_SIMILARITY:
                scores.append((doc, sim))
        
        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


def load_learned_docs() -> SemanticSearcher:
    """Load all learned documentation into the search index."""
    searcher = SemanticSearcher()
    
    if not LEARNED_DOCS_DIR.exists():
        print(f"Error: Learned docs directory not found: {LEARNED_DOCS_DIR}", file=sys.stderr)
        sys.exit(1)
    
    json_files = list(LEARNED_DOCS_DIR.glob("*.json"))
    if not json_files:
        print(f"Warning: No JSON files found in {LEARNED_DOCS_DIR}", file=sys.stderr)
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            doc_name = data.get('name', json_file.stem)
            title = data.get('title', doc_name)
            source = data.get('source', str(json_file))
            
            # Add description as a section
            if data.get('description'):
                searcher.add_document(
                    doc_id=f"{doc_name}:description",
                    title=title,
                    content=data['description'],
                    source=source,
                    section_name="Description",
                    metadata={'doc_file': str(json_file)}
                )
            
            # Add each section
            sections = data.get('sections', {})
            for section_name, content in sections.items():
                if isinstance(content, str) and content.strip():
                    searcher.add_document(
                        doc_id=f"{doc_name}:{section_name}",
                        title=title,
                        content=content,
                        source=source,
                        section_name=section_name,
                        metadata={'doc_file': str(json_file)}
                    )
            
            # Add code blocks as searchable content
            code_blocks = data.get('code_blocks', [])
            for i, block in enumerate(code_blocks):
                if isinstance(block, dict) and block.get('content'):
                    content = block['content']
                    lang = block.get('language', '')
                    # Include language in content for better matching
                    block_text = f"{lang} code example:\n{content}" if lang else content
                    searcher.add_document(
                        doc_id=f"{doc_name}:code:{i}",
                        title=title,
                        content=block_text,
                        source=source,
                        section_name=f"Code Example {i+1}",
                        metadata={'doc_file': str(json_file), 'language': lang}
                    )
            
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse {json_file}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Error loading {json_file}: {e}", file=sys.stderr)
    
    searcher.build_index()
    return searcher


def extract_relevant_snippet(content: str, query: str, max_chars: int = 400) -> str:
    """Extract the most relevant snippet from content based on query terms."""
    query_terms = set(re.findall(r'\w+', query.lower()))
    
    if len(content) <= max_chars:
        return content
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', content)
    
    # Score each sentence by number of query terms
    sentence_scores = []
    for i, sentence in enumerate(sentences):
        score = sum(1 for term in query_terms if term in sentence.lower())
        sentence_scores.append((i, sentence, score))
    
    # Find best scoring sentence
    sentence_scores.sort(key=lambda x: x[2], reverse=True)
    
    if sentence_scores and sentence_scores[0][2] > 0:
        # Start from the best sentence and expand
        best_idx = sentence_scores[0][0]
        result = sentences[best_idx]
        
        # Add surrounding sentences while under limit
        prev_idx = best_idx - 1
        next_idx = best_idx + 1
        
        while prev_idx >= 0 or next_idx < len(sentences):
            added = False
            # Try to add previous sentence
            if prev_idx >= 0:
                candidate = sentences[prev_idx] + " " + result
                if len(candidate) <= max_chars:
                    result = candidate
                    prev_idx -= 1
                    added = True
            
            # Try to add next sentence
            if next_idx < len(sentences):
                candidate = result + " " + sentences[next_idx]
                if len(candidate) <= max_chars:
                    result = candidate
                    next_idx += 1
                    added = True
            
            if not added:
                break
        
        return result
    
    # Fallback: return first part of content
    return content[:max_chars] + "..." if len(content) > max_chars else content


def synthesize_answer(query: str, results: List[Tuple[Dict, float]]) -> str:
    """Synthesize a clear answer from search results."""
    if not results:
        return "I couldn't find any relevant documentation for your question."
    
    # Group results by document for better organization
    docs_used = {}
    snippets = []
    
    for doc, score in results:
        source_key = doc.get('source', 'Unknown')
        if source_key not in docs_used:
            docs_used[source_key] = {
                'title': doc.get('title', 'Unknown'),
                'sections': []
            }
        
        content = doc.get('content', '')
        section = doc.get('section', '')
        snippet = extract_relevant_snippet(content, query)
        
        docs_used[source_key]['sections'].append({
            'section': section,
            'snippet': snippet,
            'score': score
        })
    
    # Build the answer
    lines = []
    
    # Main answer synthesis
    top_result = results[0][0]
    top_content = extract_relevant_snippet(top_result.get('content', ''), query, 600)
    
    lines.append("📚 **Answer:**")
    lines.append("")
    lines.append(top_content)
    lines.append("")
    
    # Add supporting information if available
    if len(results) > 1:
        lines.append("📝 **Additional Details:**")
        lines.append("")
        
        for doc, score in results[1:3]:  # Show top 2-3
            section = doc.get('section', '')
            content = extract_relevant_snippet(doc.get('content', ''), query, 250)
            
            if section and section != "Description":
                lines.append(f"• *{section}:* {content}")
            else:
                lines.append(f"• {content}")
            lines.append("")
    
    # Citations
    lines.append("📖 **Sources:**")
    lines.append("")
    for source, info in docs_used.items():
        # Extract just the filename from the path
        source_display = source.split('/')[-1] if '/' in source else source
        lines.append(f"• `{info['title']}` ({source_display})")
        for sec in info['sections'][:2]:  # Limit sections shown
            sec_name = sec['section'] if sec['section'] else 'overview'
            lines.append(f"  - Section: *{sec_name}*")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: claw_ask <question>")
        print("\nExamples:")
        print('  claw_ask "how do I spawn a subagent with a timeout?"')
        print('  claw_ask "what are the session tool commands?"')
        print('  claw_ask "explain multi-agent routing"')
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    print(f"🔍 Searching documentation for: \"{query}\"\n")
    
    # Load and index documents
    searcher = load_learned_docs()
    
    # Search
    results = searcher.search(query)
    
    if not results:
        print("❌ No relevant documentation found.")
        print("\nTry:")
        print("  • Using different keywords")
        print("  • Being more specific about what you're looking for")
        print("  • Checking if the documentation has been learned yet")
        sys.exit(0)
    
    # Synthesize and display answer
    answer = synthesize_answer(query, results)
    print(answer)


if __name__ == "__main__":
    main()
