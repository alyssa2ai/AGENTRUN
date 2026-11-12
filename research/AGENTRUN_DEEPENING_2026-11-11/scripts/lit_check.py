"""Query the public arXiv API for the related-work check and save the hits.

    py -3.11 scripts/lit_check.py > logs/lit_check_arxiv.txt
"""
import re
import time
import urllib.parse
import urllib.request

QUERIES = [
    ('ti:LongMemEval', 2), ('ti:MemoryAgentBench OR ti:"Evaluating Memory in LLM Agents"', 3),
    ('ti:"Evaluating Very Long-Term Conversational Memory"', 1), ('ti:FaithEval', 1), ('ti:ConflictBank', 1),
    ('ti:Zep AND ti:"Temporal Knowledge Graph"', 1), ('ti:Mem0', 2), ('ti:"Self-RAG"', 1),
    ('ti:"Corrective Retrieval Augmented Generation"', 1), ('ti:AgentPoison', 1), ('ti:MemGPT', 1),
    ('ti:"Generative Agents" AND ti:"Interactive Simulacra"', 1),
    ('abs:"agent memory" AND abs:stale AND abs:conflict', 6),
    ('abs:memory AND abs:"LLM agents" AND abs:"knowledge update" AND abs:benchmark', 6),
    ('abs:"long-term memory" AND abs:agents AND abs:provenance AND abs:verification', 6),
    ('abs:"memory" AND abs:"agents" AND abs:"contradictory" AND abs:"outdated" AND abs:retrieval', 6),
    ('ti:"knowledge conflicts" AND abs:"retrieval-augmented" AND abs:survey', 3),
]
for q, n in QUERIES:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": q, "max_results": n, "sortBy": "relevance"})
    xml = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-script"}),
                                 timeout=60).read().decode("utf-8")
    print(f"## {q}")
    for e in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        title = " ".join(re.search(r"<title>(.*?)</title>", e, re.S).group(1).split())
        aid = re.search(r"<id>(.*?)</id>", e).group(1).split("/abs/")[-1]
        pub = re.search(r"<published>(\d{4}-\d{2})", e).group(1)
        summ = " ".join(re.search(r"<summary>(.*?)</summary>", e, re.S).group(1).split())[:330]
        print(f"- arXiv:{aid} ({pub}) {title}\n    {summ}")
    print()
    time.sleep(3.2)
