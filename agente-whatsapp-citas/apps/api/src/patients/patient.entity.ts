import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  OneToMany,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';
import { Appointment } from '../appointments/appointment.entity';

@Entity('patients')
export class Patient {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  // Phone is the natural key for WhatsApp upserts; stored in E.164 (+34...).
  @Index({ unique: true })
  @Column()
  phone: string;

  @Column({ nullable: true, type: 'varchar' })
  email: string | null;

  @Column({ type: 'text', nullable: true })
  notes: string | null;

  @OneToMany(() => Appointment, (appointment) => appointment.patient)
  appointments: Appointment[];

  @CreateDateColumn({ type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ type: 'timestamptz' })
  updatedAt: Date;
}
