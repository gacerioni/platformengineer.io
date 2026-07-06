---
slug: rate-limiting-llms-token-bucket-redis
title: Rate limiting LLMs with a token bucket in Redis
summary: A gateway and one Lua script turn a runaway token bill into a control plane.
tags: llm, rate-limiting, redis, ai-infra
published_at: 2026-05-20
reading_minutes: 8
draft: false
---
Most LLM cost blowups are not a pricing problem, they are a concurrency problem. A handful of clients, a retry loop, an agent that fans out, and suddenly you are paying for ten times the tokens you meant to spend, with no single place that saw it coming.

A gateway with a token bucket in Redis fixes that, and it turns out to be a small amount of code.

## Why a token bucket, and why Redis

A token bucket is the right shape for this. You refill tokens at a steady rate up to a cap, and every request spends some. Bursts are allowed up to the cap, sustained load is capped at the refill rate. That maps cleanly onto "this tenant gets N thousand tokens per minute, bursts welcome, no runaway."

Redis is the right home for the bucket because the check has to be atomic and shared across every gateway instance. One key per tenant or per model, updated in place, visible to all workers. No sticky sessions, no per-process state to reconcile.

## The atomic refill

Do the refill and the spend in one Lua script, so two concurrent requests can never both see a full bucket:

```lua
-- KEYS[1] = bucket, ARGV = rate, cap, now, cost
local b = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(b[1]) or tonumber(ARGV[2])
local ts = tonumber(b[2]) or tonumber(ARGV[3])
local delta = math.max(0, tonumber(ARGV[3]) - ts) * tonumber(ARGV[1])
tokens = math.min(tonumber(ARGV[2]), tokens + delta)
if tokens < tonumber(ARGV[4]) then return 0 end
redis.call('HMSET', KEYS[1], 'tokens', tokens - tonumber(ARGV[4]), 'ts', ARGV[3])
return 1
```

One call, no race, same behavior whether you run one gateway or twenty.

## The gauntlet

Rate limiting is one stage of a short pipeline every request runs before it is allowed to cost money:

1. Router picks the model for the task, so cheap requests do not hit the expensive model.
2. Cache checks whether a semantically equivalent request was already answered, and returns it if so.
3. Budget runs the token bucket, per tenant and per model.
4. Model is called only if the request survived the first three.

Each stage is a Redis lookup measured in microseconds, so the gauntlet adds almost nothing to latency while removing most of the waste.

## What you get for free

Because every request passes through one place backed by Redis, you also get the things people usually bolt on later: per-tenant fairness, live spend counters, and a kill switch that is one key away. The rate limiter stops being a defensive patch and becomes the control plane for how the whole system spends tokens.
