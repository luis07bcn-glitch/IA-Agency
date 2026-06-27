// Curated shortlist shown by default in the model dropdown. The UI can also
// request the full live catalog ("ver todos").
export const CURATED_MODELS: { id: string; label: string }[] = [
  { id: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet (recomendado)' },
  { id: 'anthropic/claude-3.5-haiku', label: 'Claude 3.5 Haiku (rapido y barato)' },
  { id: 'openai/gpt-4o', label: 'GPT-4o' },
  { id: 'openai/gpt-4o-mini', label: 'GPT-4o mini (rapido y barato)' },
  { id: 'google/gemini-2.0-flash-001', label: 'Gemini 2.0 Flash' },
  { id: 'meta-llama/llama-3.3-70b-instruct', label: 'Llama 3.3 70B' },
];

export interface OpenRouterModel {
  id: string;
  label: string;
}

// Fetches the live OpenRouter catalog. Public endpoint, no key required.
export async function fetchOpenRouterCatalog(): Promise<OpenRouterModel[]> {
  const res = await fetch('https://openrouter.ai/api/v1/models', {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`OpenRouter respondio ${res.status}`);
  }
  const json = (await res.json()) as { data?: { id: string; name?: string }[] };
  return (json.data ?? [])
    .map((m) => ({ id: m.id, label: m.name || m.id }))
    .sort((a, b) => a.label.localeCompare(b.label));
}
