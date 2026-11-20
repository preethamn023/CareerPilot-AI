/**
 * CareerPilot AI - Local AI Bridge
 * --------------------------------
 * A tiny HTTP bridge that exposes the sandbox LLM (z-ai-web-dev-sdk) as an
 * OpenAI-style chat endpoint for the Python FastAPI backend.
 *
 * Used ONLY as a fallback when GEMINI_API_KEY is not configured, so the
 * application keeps its full AI functionality in this demo environment.
 * Binds to 127.0.0.1 only - never exposed externally.
 */
import ZAI from 'z-ai-web-dev-sdk';

const PORT = 8010;
const HOST = '127.0.0.1';

let client: Awaited<ReturnType<typeof ZAI.create>> | null = null;

async function getClient() {
  if (!client) {
    client = await ZAI.create();
    console.log('[ai-bridge] ZAI client initialised');
  }
  return client;
}

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

const server = Bun.serve({
  port: PORT,
  hostname: HOST,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === '/health') {
      return Response.json({ status: 'ok', service: 'careerpilot-ai-bridge' });
    }

    if (req.method === 'POST' && url.pathname === '/v1/chat/completions') {
      let body: { messages?: ChatMessage[] };
      try {
        body = await req.json();
      } catch {
        return Response.json({ error: 'invalid JSON body' }, { status: 400 });
      }
      const messages = (body.messages || []).filter(
        (m) => m && typeof m.role === 'string' && typeof m.content === 'string' && m.content.length > 0
      );
      if (messages.length === 0) {
        return Response.json({ error: 'messages array is required' }, { status: 400 });
      }

      try {
        const zai = await getClient();
        const completion = await zai.chat.completions.create({
          messages,
          thinking: { type: 'disabled' },
        });
        const content: string = completion.choices?.[0]?.message?.content ?? '';
        if (!content) {
          return Response.json({ error: 'empty completion' }, { status: 502 });
        }
        return Response.json({ content, model: completion.model ?? 'glm' });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        console.error('[ai-bridge] completion failed:', message);
        return Response.json({ error: 'completion failed' }, { status: 500 });
      }
    }

    return Response.json({ error: 'not found' }, { status: 404 });
  },
});

console.log(`[ai-bridge] listening on http://${HOST}:${PORT}`);
