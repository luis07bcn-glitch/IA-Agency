import { Injectable, Logger } from '@nestjs/common';
import * as http from 'http';
import * as WebSocket from 'ws';
import { AgentService } from '../agent/agent.service';
import { ConfigService } from '../config/config.service';

interface CallSession {
  callSid: string;
  callerNumber: string;
  history: { role: 'user' | 'assistant'; content: string }[];
}

/**
 * WebSocket server for Twilio ConversationRelay.
 *
 * Twilio opens a WSS connection per call. On each "prompt" message (caller
 * spoke), we run the agent and stream back a "text" token so Twilio TTS
 * speaks the response aloud.
 *
 * This is NOT a NestJS @WebSocketGateway — we mount it manually on the
 * same HTTP server so it can share the /api prefix without conflicting with
 * Mastra's catch-all routes.
 */
@Injectable()
export class VoiceGateway {
  private readonly logger = new Logger('VoiceGateway');
  private wss: WebSocket.Server | null = null;

  constructor(
    private readonly agentService: AgentService,
    private readonly configService: ConfigService,
  ) {}

  /** Called from main.ts after the HTTP server is created. */
  attachToServer(server: http.Server): void {
    this.wss = new WebSocket.Server({ noServer: true });

    server.on('upgrade', (req, socket, head) => {
      if (req.url === '/api/voice/ws') {
        this.wss!.handleUpgrade(req, socket as any, head, (ws) => {
          this.wss!.emit('connection', ws, req);
        });
      }
    });

    this.wss.on('connection', (ws) => this.handleConnection(ws));
    this.logger.log('VoiceGateway WebSocket listo en /api/voice/ws');
  }

  private handleConnection(ws: WebSocket.WebSocket): void {
    const session: CallSession = {
      callSid: '',
      callerNumber: '',
      history: [],
    };

    ws.on('message', async (raw) => {
      let msg: Record<string, any>;
      try {
        msg = JSON.parse(raw.toString());
      } catch {
        return;
      }

      switch (msg.type) {
        case 'setup':
          session.callSid = msg.callSid ?? '';
          session.callerNumber = msg.customParameters?.callerNumber ?? msg.from ?? '';
          this.logger.log(`Llamada conectada: ${session.callSid} desde ${session.callerNumber}`);
          break;

        case 'prompt':
          if (!msg.last) return; // wait for the full utterance
          await this.handlePrompt(ws, session, msg.voicePrompt as string);
          break;

        case 'interrupt':
          // Caller interrupted — Twilio discards previous TTS, we just log.
          this.logger.debug('Interrupción del caller');
          break;

        case 'error':
          this.logger.error(`Error de ConversationRelay: ${msg.description}`);
          break;
      }
    });

    ws.on('close', () => {
      this.logger.log(`Llamada terminada: ${session.callSid}`);
    });
  }

  private async handlePrompt(
    ws: WebSocket.WebSocket,
    session: CallSession,
    userText: string,
  ): Promise<void> {
    this.logger.log(`[${session.callSid}] Caller: "${userText}"`);
    session.history.push({ role: 'user', content: userText });

    try {
      const reply = await this.agentService.generateReplyForVoice(session.history);

      session.history.push({ role: 'assistant', content: reply });
      this.logger.log(`[${session.callSid}] Agente: "${reply}"`);

      // Check if the agent wants to end the call.
      const shouldHangup = /hasta luego|adiós|gracias.*llamar/i.test(reply);
      this.sendText(ws, reply, shouldHangup);
    } catch (err) {
      this.logger.error('Error generando respuesta de voz:', err);
      this.sendText(ws, 'Disculpa, ha habido un problema técnico. Por favor, vuelve a llamar en unos minutos.');
    }
  }

  /** Sends a text token to Twilio ConversationRelay (TTS). */
  private sendText(ws: WebSocket.WebSocket, text: string, endCall = false): void {
    if (ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: 'text', token: text, last: true }));
    if (endCall) {
      setTimeout(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'end' }));
        }
      }, 1000);
    }
  }
}
