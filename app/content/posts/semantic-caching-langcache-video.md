---
slug: semantic-caching-langcache-video
title: Cut your LLM bill with semantic caching (video)
summary: A live walkthrough of Redis LangCache: serve semantically repeated questions from cache in milliseconds, with the token savings adding up on screen.
tags: llm, semantic-cache, redis, finops, video
published_at: 2026-07-12
reading_minutes: 4
draft: false
---
If your AI app answers the same question hundreds of times a day, you are paying the LLM hundreds of times for the same answer. Semantic caching fixes that, and I recorded a full walkthrough of how it works, end to end.

<div style="position:relative;width:100%;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;margin:10px 0 6px"><iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border:0" src="https://www.youtube-nocookie.com/embed/Ykf69qIxp24" title="Redis LangCache: semantic caching demo" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>

The walkthrough is in Brazilian Portuguese.

## What semantic caching is

Before calling the LLM, you ask the cache one question: has anyone already asked something close enough to this? If yes, you return the stored answer in milliseconds and spend zero tokens. If no, you call the model and store the answer for next time. Search before, store after, two API calls.

The key word is semantic. "What is machine learning", "explain ML to me", and the same question in another language are three different strings but one meaning, so they should cost one generation, not three.

## What the video walks through

- The LangCache service on Redis Cloud: automatic embeddings, a similarity threshold you tune per request, TTL, and custom attributes to scope the cache.
- A live demo where cache memories are scoped per person, per business unit, and company-wide, with no answer leaking across the wrong scope.
- A multilingual hit: the same question in a different language and phrasing still lands on the cached answer, because the match is on meaning, not on the string.
- Under the hood in Redis Insight: each cache entry is a plain hash (prompt, response, attributes, embedding), and the Profiler shows the whole lookup is one hybrid `FT.SEARCH`, an attribute filter plus a vector KNN in a single command.

## The math

Savings are simple: output token cost times your cache hit rate. In FAQ, support, and assistant traffic, a real slice of questions is semantically repeated, so you stop paying to generate those answers again and again.

Large customers running semantic caching in production have seen 30%+ token savings. That is an observed result, never a guarantee. The part I like most: it scales with success. The more your app grows, the more repeated questions arrive, the more the cache hits.

## Try it

- [Live demo](https://langcache.platformengineer.io/)
- [Demo source code](https://github.com/Redislabs-Solution-Architects/redis-langcache-python-example)
- [LangCache docs](https://redis.io/docs/latest/develop/ai/context-engine/langcache/)
- [Savings calculator](https://redis.io/calculator/langcache/)

Run it against your own traffic, measure the hit rate, and tell me what you see.
