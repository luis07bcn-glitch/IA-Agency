import {
  Column,
  CreateDateColumn,
  Entity,
  JoinColumn,
  ManyToOne,
  PrimaryGeneratedColumn,
} from 'typeorm';
import { Conversation } from './conversation.entity';

export type MessageRole = 'user' | 'assistant' | 'system';

@Entity('messages')
export class Message {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ManyToOne(() => Conversation, (conversation) => conversation.messages, {
    onDelete: 'CASCADE',
    nullable: false,
  })
  @JoinColumn({ name: 'conversation_id' })
  conversation: Conversation;

  @Column({ name: 'conversation_id' })
  conversationId: string;

  @Column({ type: 'varchar' })
  role: MessageRole;

  @Column({ type: 'text' })
  text: string;

  @CreateDateColumn({ type: 'timestamptz' })
  createdAt: Date;
}
