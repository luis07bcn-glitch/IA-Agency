/**
 * Minimal, dependency-free LLM call shared by non-agent features (insights,
 * demo builder, etc). Branches on the key: Anthropic direct vs OpenRouter.
 * The agent itself uses Mastra + tools; this is only for plain text generation.
 */
export interface LlmMessage {
  role: 'user' | 'assistant';
  content: string;
}

export async function callLLM(opts: {
  apiKey: string;
  model: string;
  system: string;
  messages: LlmMessage[];
  maxTokens: number;
}): Promise<string> {
  const { apiKey, model, system, messages, maxTokens } = opts;

  if (apiKey.startsWith('sk-ant-')) {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({ model, max_tokens: maxTokens, system, messages }),
    });
    if (!res.ok) throw new Error(`Anthropic ${res.status}: ${await res.text()}`);
    const data = (await res.json()) as { content: { type: string; text?: string }[] };
    return (data.content.find((b) => b.type === 'text')?.text ?? '').trim();
  }

  // OpenRouter (OpenAI-compatible).
  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      messages: [{ role: 'system', content: system }, ...messages],
    }),
  });
  if (!res.ok) throw new Error(`OpenRouter ${res.status}: ${await res.text()}`);
  const data = (await res.json()) as any;
  return (data.choices?.[0]?.message?.content ?? '').trim();
}

/** Extracts the first JSON object/array from an LLM response (handles code fences). */
export function parseLlmJson<T = any>(raw: string): T {
  let s = raw.trim();
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence) s = fence[1].trim();
  const startObj = s.indexOf('{');
  const startArr = s.indexOf('[');
  const start =
    startArr === -1 ? startObj : startObj === -1 ? startArr : Math.min(startObj, startArr);
  const end = Math.max(s.lastIndexOf('}'), s.lastIndexOf(']'));
  if (start === -1 || end === -1) throw new Error('Respuesta sin JSON.');
  return JSON.parse(s.slice(start, end + 1)) as T;
}
