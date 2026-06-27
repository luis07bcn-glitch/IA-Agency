import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  JoinColumn,
  ManyToOne,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';
import { Patient } from '../patients/patient.entity';

export type AppointmentStatus =
  | 'scheduled'
  | 'completed'
  | 'cancelled'
  | 'no_show';

export type AppointmentSource = 'manual' | 'agent';

@Entity('appointments')
export class Appointment {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  // An appointment ALWAYS belongs to a patient.
  @ManyToOne(() => Patient, (patient) => patient.appointments, {
    onDelete: 'CASCADE',
    nullable: false,
    eager: true,
  })
  @JoinColumn({ name: 'patient_id' })
  patient: Patient;

  @Column({ name: 'patient_id' })
  patientId: string;

  @Column()
  serviceName: string;

  @Index()
  @Column({ type: 'timestamptz' })
  startsAt: Date;

  @Column({ type: 'timestamptz' })
  endsAt: Date;

  @Column({ type: 'varchar', default: 'scheduled' })
  status: AppointmentStatus;

  @Column({ type: 'varchar', default: 'manual' })
  source: AppointmentSource;

  @Column({ type: 'text', nullable: true })
  notes: string | null;

  // Reminder bookkeeping so we never send the same reminder twice.
  @Column({ default: false })
  reminder24Sent: boolean;

  @Column({ default: false })
  reminder2Sent: boolean;

  @Column({ default: false })
  noShowRecoverySent: boolean;

  @CreateDateColumn({ type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ type: 'timestamptz' })
  updatedAt: Date;
}
