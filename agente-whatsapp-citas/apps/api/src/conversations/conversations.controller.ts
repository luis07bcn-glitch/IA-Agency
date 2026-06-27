import { Controller, Get, Param, Query } from '@nestjs/common';
import { ConversationsService } from './conversations.service';

@Controller('conversations')
export class ConversationsController {
  constructor(private readonly conversations: ConversationsService) {}

  // GET /api/conversations  -> list of threads (inbox)
  @Get()
  list(@Query('limit') limit?: string) {
    return this.conversations.listThreads(limit ? Number(limit) : 100);
  }

  // GET /api/conversations/:id/messages  -> messages of a thread
  @Get(':id/messages')
  messages(@Param('id') id: string) {
    return this.conversations.getMessages(id);
  }
}
