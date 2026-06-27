import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Conversation, ConversationChannel } from './conversation.entity';
import { Message, MessageRole } from './message.entity';
import { EventsService } from '../events/events.service';

@Injectable()
export class ConversationsService {
  constructor(
    @InjectRepository(Conversation)
    private readonly conversations: Repository<Conversation>,
    @InjectRepository(Message)
    private readonly messages: Repository<Message>,
    private readonly events: EventsService,
  ) {}

  listThreads(limit = 100): Promise<Conversation[]> {
    return this.conversations.find({
      order: { lastMessageAt: 'DESC' },
      take: limit,
    });
  }

  recent(limit = 5): Promise<Conversation[]> {
    return this.listThreads(limit);
  }

  async getThread(id: string): Promise<Conversation> {
    const thread = await this.conversations.findOne({ where: { id } });
    if (!thread) throw new NotFoundException('Conversacion no encontrada');
    return thread;
  }

  getMessages(conversationId: string): Promise<Message[]> {
    return this.messages.find({
      where: { conversationId },
      order: { createdAt: 'ASC' },
    });
  }

  async getOrCreateWhatsappThread(
    phone: string,
    patientId: string | null,
    title?: string,
  ): Promise<Conversation> {
    let thread = await this.conversations.findOne({
      where: { phone, channel: 'whatsapp' },
    });
    if (!thread) {
      thread = this.conversations.create({
        phone,
        patientId,
        channel: 'whatsapp',
        title: title ?? phone,
        lastMessageAt: new Date(),
      });
      thread = await this.conversations.save(thread);
      this.events.emit('conversation.changed', { id: thread.id });
    } else if (patientId && !thread.patientId) {
      thread.patientId = patientId;
      thread = await this.conversations.save(thread);
    }
    return thread;
  }

  async createThread(
    channel: ConversationChannel,
    title: string,
    patientId: string | null = null,
  ): Promise<Conversation> {
    const thread = await this.conversations.save(
      this.conversations.create({
        channel,
        title,
        patientId,
        phone: null,
        lastMessageAt: new Date(),
      }),
    );
    this.events.emit('conversation.changed', { id: thread.id });
    return thread;
  }

  async addMessage(
    conversationId: string,
    role: MessageRole,
    text: string,
  ): Promise<Message> {
    const msg = await this.messages.save(
      this.messages.create({ conversationId, role, text }),
    );
    await this.conversations.update(conversationId, {
      lastMessageAt: msg.createdAt,
    });
    this.events.emit('message.created', { conversationId });
    this.events.emit('conversation.changed', { id: conversationId });
    return msg;
  }

  /** Returns the message history formatted for the agent (role/content). */
  async historyForAgent(
    conversationId: string,
    limit = 20,
  ): Promise<{ role: 'user' | 'assistant'; content: string }[]> {
    const msgs = await this.messages.find({
      where: { conversationId },
      order: { createdAt: 'DESC' },
      take: limit,
    });
    return msgs
      .reverse()
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.text,
      }));
  }
}
