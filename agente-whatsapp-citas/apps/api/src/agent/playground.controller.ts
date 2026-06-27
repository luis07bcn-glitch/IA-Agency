import { Body, Controller, Post } from '@nestjs/common';
import { IsOptional, IsString, MinLength } from 'class-validator';
import { AgentService } from './agent.service';
import { ConversationsService } from '../conversations/conversations.service';
import { PatientsService } from '../patients/patients.service';

class PlaygroundDto {
  @IsString()
  @MinLength(1)
  message: string;

  @IsOptional()
  @IsString()
  conversationId?: string;
}

@Controller('agent')
export class PlaygroundController {
  constructor(
    private readonly agent: AgentService,
    private readonly conversations: ConversationsService,
    private readonly patients: PatientsService,
  ) {}

  // POST /api/agent/playground -> chat with the agent inside the app (no WhatsApp)
  @Post('playground')
  async playground(@Body() dto: PlaygroundDto) {
    // The playground uses a synthetic "test" patient so booking tools work.
    const patient = await this.patients.upsertByPhone(
      '+34000000000',
      'Paciente de prueba (Playground)',
    );

    let conversationId = dto.conversationId;
    if (!conversationId) {
      const thread = await this.conversations.createThread(
        'playground',
        'Playground',
        patient.id,
      );
      conversationId = thread.id;
    }

    await this.conversations.addMessage(conversationId, 'user', dto.message);
    const history = await this.conversations.historyForAgent(conversationId);

    const reply = await this.agent.generateReply({
      conversationId,
      patient,
      history: history.slice(0, -1), // history excludes the message we just added
      userText: dto.message,
    });

    await this.conversations.addMessage(conversationId, 'assistant', reply);

    return { conversationId, reply };
  }
}
