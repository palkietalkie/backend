-- OpenAI realtime $ cost per session, stored (product decision) rather than derived on read: input_tokens/output_tokens x the model's audio $/M rate at end time. A rate change needs a backfill. Ongoing cost math's source of truth is app/services/openai/compute_realtime_cost.py; the backfill below inlines the same rates as a one-time historical snapshot for the sessions already recorded.
ALTER TABLE conversation_sessions
    ADD COLUMN input_cost_usd numeric(10, 6),
    ADD COLUMN output_cost_usd numeric(10, 6);

UPDATE conversation_sessions
SET input_cost_usd = input_tokens / 1000000.0 * CASE model
        WHEN 'gpt-realtime-mini' THEN 10.0
        WHEN 'gpt-realtime-2' THEN 32.0
        WHEN 'gpt-realtime' THEN 32.0
    END,
    output_cost_usd = output_tokens / 1000000.0 * CASE model
        WHEN 'gpt-realtime-mini' THEN 20.0
        WHEN 'gpt-realtime-2' THEN 64.0
        WHEN 'gpt-realtime' THEN 64.0
    END
WHERE input_tokens IS NOT NULL
  AND model IN ('gpt-realtime-mini', 'gpt-realtime-2', 'gpt-realtime');
