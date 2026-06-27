import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  JoinColumn,
  ManyToOne,
  OneToMany,
  PrimaryGeneratedColumn,
} from 'typeorm';
import { Patient } from '../patients/patient.entity';
import { Message } from './message.entity';

export type ConversationChannel = 'whatsapp' | 'playground';

@Entity('conversations')
export class Conversation {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  // A conversation may exist before we know the patient (first WhatsApp message).
  @ManyToOne(() => Patient, { nullable: true, onDelete: 'SET NULL', eager: true })
  @JoinColumn({ name: 'patient_id' })
  patient: Patient | null;

  @Column({ name: 'patient_id', nullable: true, type: 'uuid' })
  patientId: string | null;

  @Column({ type: 'varchar', default: 'whatsapp' })
  channel: ConversationChannel;

  // For WhatsApp threads we key by phone; null for playground.
  @Index()
  @Column({ type: 'varchar', nullable: true })
  phone: string | null;

  @Column({ type: 'varchar', nullable: true })
  title: string | null;

  @Index()
  @Column({ type: 'timestamptz' })
  lastMessageAt: Date;

  @OneToMany(() => Message, (message) => message.conversation)
  messages: Message[];

  @CreateDateColumn({ type: 'timestamptz' })
  createdAt: Date;
}
