---
slug: feature-store-redis-vs-dynamodb
title: Why your online feature store belongs in Redis, not DynamoDB
summary: Fan-out and the p99 tail are what break online feature serving, and why Redis sits above the warehouse as the hot tier.
tags: feature-store, redis, dynamodb, fraud
published_at: 2026-06-15
reading_minutes: 6
draft: false
---
The online feature store is a latency problem dressed as a data problem. When a fraud model scores a transaction, it has a few milliseconds to pull dozens of features at once: velocity counters, one-minute aggregates, the last known device, a running risk score. Miss the budget and you either block a good customer or wave through a bad one.

The usual default for that serving layer is DynamoDB. It is managed, it scales, and it is already in the account. But "it scales" and "it holds a tight p99 under real fan-out" are not the same sentence.

## Where the default gets expensive

A single scoring decision rarely reads one item. It reads many, one per feature group, and it does that for every transaction. At a few thousand decisions per second with dozens of features each, the read volume multiplies fast, and so does the bill. Then the p99 creeps up, so a cache goes in front, and now the architecture is quietly admitting that the store underneath was never fast enough for the online path.

That is the tell. When the answer to a latency problem is "put a cache in front of it," the cache is the real serving tier. You may as well design for that from the start.

## Redis as the premium online tier

The move is not to replace the offline store. Keep the warehouse and the batch pipelines where they are. Add Redis as the hot online tier that the model actually reads from, and let native data structures do the work:

- Hashes hold a feature vector as one keyed object, read in a single round trip.
- Sorted sets carry time-window aggregates, trimmed by score, so a one-minute count is a range query, not a scan.
- Counters with TTL give you velocity features and freshness for free.
- Pipelines and Lua collapse "read twelve features" into one network hop, evaluated atomically.

The result is sub-millisecond reads on the serving path, with the fan-out handled inside Redis instead of across a dozen calls.

## The pattern that ships

Source of record stays where it is: the warehouse, or DynamoDB if that is your system of record. Streaming change data capture feeds Redis in near real time, so the online features are fresh without a nightly job. The model reads only Redis. If a key is missing, you fall back and repair, but the hot path never leaves memory.

I have run this for fraud at around nine thousand decisions per second. The interesting part was not the peak throughput, it was the tail: the p99 stayed flat while the feature count per decision grew, because the cost was one round trip regardless of how many features rode along.

## When not to bother

If your QPS is modest and your latency budget is relaxed, a single store is fine, and adding a tier is just more to operate. This pattern earns its keep when fan-out is high and the tail matters, which is exactly when fraud, risk, and real-time personalization live or die.
